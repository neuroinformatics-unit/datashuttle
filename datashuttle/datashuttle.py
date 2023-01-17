from __future__ import annotations

import copy
import glob
import json
import os
import shutil
from collections.abc import ItemsView
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import paramiko

from datashuttle.configs import canonical_directories, load_configs
from datashuttle.configs.configs import Configs
from datashuttle.utils import (
    directories,
    ds_logger,
    formatting,
    rclone,
    ssh,
    utils,
)
from datashuttle.utils.decorators import (  # noqa
    check_configs_set,
    requires_ssh_configs,
)

# --------------------------------------------------------------------------------------------------------------------
# Project Manager Class
# --------------------------------------------------------------------------------------------------------------------


class DataShuttle:
    """
    DataShuttle is a tool for convenient scientific
    project management and data transfer in BIDS format.

    The expected organisation is a central repository
    on a remote machine  ('remote') that contains all
    project data. This is connected to multiple local
    machines ('local'). These can each contain a subset of
    the full project (e.g. machine for electrophysiology
    collection, machine for behavioural collection).

    On first use on a new profile, show warning prompting
    to set configurations with the function make_config_file().

    Datashuttle will save logs to a .datashuttle folder
    in the main local project. These logs contain
    detailed information on directory creation / transfer.
    To get the path to datashuttle logs, use
    get_logging_path().

    For transferring data between a remote data storage
    with SSH, use setup setup_ssh_connection_to_remote_server().
    This will allow you to check the server key, add host key to
    profile if accepted, and setup ssh key pair.

    Parameters
    ----------

    project_name : The project name to use the datashuttle
                   Directories containing all project files
                   and folderes are specified in make_config_file().
                   Datashuttle-related files are stored in
                   a .datashuttle directory in the user home
                   directory. Use get_datashuttle_path() to
                   see the path to this directory.
    """

    def __init__(self, project_name: str):

        if " " in project_name:
            utils.log_and_raise_error("project_name must not include spaces.")

        self.project_name = project_name
        (
            self._datashuttle_path,
            self._temp_log_path,
        ) = utils.get_datashuttle_path(self.project_name)
        self._config_path = self._make_path("datashuttle", "config.yaml")
        self._top_level_dir_name = "rawdata"

        self.cfg: Any = None
        self._ssh_key_path: Any = None
        self._data_type_dirs: Any = None

        self.cfg = load_configs.make_config_file_attempt_load(
            self._config_path
        )

        if self.cfg:
            self._set_attributes_after_config_load()

        rclone.prompt_rclone_download_if_does_not_exist()

    def _set_attributes_after_config_load(self) -> None:
        """
        Once config file is loaded, update all private attributes
        according to config contents.
        """
        self._project_metadata_path = self.cfg["local_path"] / ".datashuttle"

        self._make_project_metadata_if_does_not_exist()

        self._logging_path = self.make_and_get_logging_path()

        self._ssh_key_path = self._make_path(
            "datashuttle", self.project_name + "_ssh_key"
        )
        self._hostkeys_path = self._make_path("datashuttle", "hostkeys")

        self._data_type_dirs = canonical_directories.get_directories(self.cfg)

    # --------------------------------------------------------------------------------------------------------------------
    # Public Directory Makers
    # --------------------------------------------------------------------------------------------------------------------

    @check_configs_set
    def make_sub_dir(
        self,
        sub_names: Union[str, list],
        ses_names: Optional[Union[str, list]] = None,
        data_type: str = "all",
    ) -> None:
        """
        Create a subject / session directory tree in the project
        folder.

        Parameters
        ----------

        sub_names :
                subject name / list of subject names to make
                within the top-level project directory
                (if not already, these will be prefixed with
                "sub-")
        ses_names :
                (Optional). session name / list of session names.
                (if not already, these will be prefixed with
                "ses-"). If no session is provided, no session-level
                directories are made.
        data_type :
                The data_type to make in the sub / ses directories.
                (e.g. "ephys", "behav", "histology"). Only data_types
                that are enabled in the configs (e.g. use_behav) will be
                created. If "all" is selected, directories will be created
                for all data_type enabled in config. Use empty string "" for
                none.

        Notes
        -----

        sub_names or ses_names may contain formatting tags

            @TO@ :
                used to make a range of subjects / sessions.
                Boundaries of the range must be either side of the tag
                e.g. sub-001@TO@003 will generate ["sub-001", "sub-002", "sub-003"]

            @DATE@, @TIME@ @DATETIME@ :
                will add date-<value>, time-<value> or
                date-<value>_time-<value> keys respectively. Only one per-name
                is permitted. e.g. sub-001_@DATE@ will generate sub-001_date-20220101
                (on the 1st january, 2022).

        Examples
        --------
        project.make_sub_dir("sub-001", data_type="all")

        project.make_sub_dir("sub-002@TO@005",
                             ["ses-001", "ses-002"],
                             ["ephys", "behav"])
        """
        self._start_log("make_sub_dir")

        utils.log("\nFormatting Names...")
        ds_logger.log_names(["sub_names", "ses_names"], [sub_names, ses_names])

        sub_names = self._format_names(sub_names, "sub")

        if ses_names is not None:
            ses_names = self._format_names(ses_names, "ses")

        ds_logger.log_names(
            ["formatted_sub_names", "formatted_ses_names"],
            [sub_names, ses_names],
        )

        directories.check_no_duplicate_sub_ses_key_values(
            self,
            base_dir=self._get_base_and_top_level_dir("local"),
            new_sub_names=sub_names,
            new_ses_names=ses_names,
        )

        if ses_names is None:
            ses_names = []

        utils.log("\nMaking directories...")
        self._make_directory_trees(
            sub_names,
            ses_names,
            data_type,
            log=True,
        )

        utils.log("\nFinished file creation. Local folder tree is now:\n")
        ds_logger.log_tree(self.cfg["local_path"])

        utils.message_user(
            f"Finished making directories. For log of all created "
            f"directories, pleasee see {self._logging_path}"
        )

    # --------------------------------------------------------------------------------------------------------------------
    # Public File Transfer
    # --------------------------------------------------------------------------------------------------------------------

    def upload_data(
        self,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        data_type: str = "all",
        dry_run: bool = False,
        init_log: bool = True,
    ) -> None:
        """
        Upload data from a local project to the remote project
        directory. In the case that a file / directory exists on
        the remote and local, the remote will not be overwritten
        even if the remote file is an older version. Data
        transfer logs are saved to the logging directory (get_logging_path()).

        Parameters
        ----------

        sub_names :
            a subject name / list of subject names. These must
            be prefixed with "sub-", or the prefix will be
            automatically added. "@*@" can be used as a wildcard.
            "all" will search for all subdirectories in the
            data type directory to upload.
        ses_names :
            a session name / list of session names, similar to
            sub_names but requring a "ses-" prefix.
        dry_run :
            perform a dry-run of upload. This will output as if file
            transfer was taking place, but no files will be moved. Useful
            to check which files will be moved on data transfer.
        data_type :
            see make_sub_dir()

        init_log :
            (Optional). Whether to start the logger. This should
            always be True, unless logger has already been started
            (e.g. in a calling function).

        Notes
        -----

        sub_names or ses_names may contain certain formatting tags:

        @*@: wildcard search for subject names. e.g. ses-001_date-@*@
             will transfer all session 001 collected on all dates.
        @TO@: used to transfer a range of sub/ses. Number must be either side of the tag
              e.g. sub-001@TO@003 will generate ["sub-001", "sub-002", "sub-003"]
        @DATE@, @TIME@ @DATETIME@: will add date-<value>, time-<value> or
              date-<value>_time-<value> keys respectively. Only one per-name
              is permitted. e.g. sub-001_@DATE@ will generate sub-001_date-20220101
              (on the 1st january, 2022).
        """
        if init_log:
            self._start_log("upload_data")

        self._transfer_sub_ses_data(
            "upload",
            sub_names,
            ses_names,
            data_type,
            dry_run,
            log=True,
        )

    def download_data(
        self,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        data_type: str = "all",
        dry_run: bool = False,
        init_log: bool = True,
    ) -> None:
        """
        Download data from the remote project directory to the
        local project directory. In the case that a file / directory
        exists on the remote and local, the local will
        not be overwritten even if the remote file is an
        older version.

        This function is identical to upload_data() but with the direction
        of data transfer reversed. Please see upload_data() for arguments.
        "all" arguments will search the remote project for sub / ses to download.
        """
        if init_log:
            self._start_log("download_data")

        self._transfer_sub_ses_data(
            "download",
            sub_names,
            ses_names,
            data_type,
            dry_run,
            log=True,
        )

    def upload_all(self):
        """
        Convenience function to upload all data.

        Alias for:
            project.upload_data("all", "all", "all")
        """
        self._start_log("upload_all")

        self.upload_data("all", "all", "all", init_log=False)

    def download_all(self):
        """
        Convenience function to download all data.

        Alias for : project.download_data("all", "all", "all")
        """
        self._start_log("download_all")

        self.download_data("all", "all", "all", init_log=False)

    def upload_project_dir_or_file(
        self, filepath: str, dry_run: bool = False
    ) -> None:
        """
        Upload a single, specified directory (including all subdirectories
        and files) from the local to the remote machine.

        Parameters
        ----------

        filepath :
            a string containing the filepath to move,
            relative to the project directory "rawdata"
            or "derivatives" path (depending on which is currently
            set). Alternatively, the entire path is accepted.
        dry_run :
            perform a dry-run of upload. This will output as if file
            transfer was taking place, but no files will be moved. Useful
            to check which files will be moved on data transfer.
        """
        self._start_log("upload_project_dir_or_file")

        processed_filepath = utils.get_path_after_base_dir(
            self._get_base_dir("local") / self._top_level_dir_name,
            Path(filepath),
        )

        self._move_dir_or_file(
            processed_filepath.as_posix(),
            "upload",
            dry_run,
            log=True,
        )

    def download_project_dir_or_file(
        self, filepath: str, dry_run: bool = False
    ) -> None:
        """
        Download an entire directory (including all subdirectories
        and files) from the remote to the local machine.

        This method is identical to upload_project_dir_or_file
        but with direction of transfer reversed. Please see
        upload_project_dir_or_file() for arguments.
        """
        self._start_log("download_project_dir_or_file")

        processed_filepath = utils.get_path_after_base_dir(
            self._get_base_dir("remote") / self._top_level_dir_name,
            Path(filepath),
        )
        self._move_dir_or_file(
            processed_filepath.as_posix(),
            "download",
            dry_run,
            log=True,
        )

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    @requires_ssh_configs
    def setup_ssh_connection_to_remote_server(self) -> None:
        """
        Setup a connection to the remote server using SSH.
        Assumes the remote_host_id and remote_host_username
        are set in configs (see make_config_file() and update_config())

        First, the server key will be displayed, requiring
        verification of the server ID. This will store the
        hostkey for all future use.

        Next, prompt to input their password for the remote
        cluster. Once input, SSH private / public key pair
        will be setup.
        """
        self._start_log("setup_ssh_connection_to_remote_server")

        verified = ssh.verify_ssh_remote_host(
            self.cfg["remote_host_id"],
            self._hostkeys_path,
            log=True,
        )

        if verified:
            self._setup_ssh_key_and_rclone_config(log=True)

    def write_public_key(self, filepath: str) -> None:
        """
        By default, the SSH private key only is stored, in
        the datashuttle configs directory. Use this function
        to save the public key.

        Parameters
        ----------

        filepath :
            full filepath (inc filename) to write the
            public key to.
        """
        key = paramiko.RSAKey.from_private_key_file(
            self._ssh_key_path.as_posix()
        )

        with open(filepath, "w") as public:
            public.write(key.get_base64())
        public.close()

    # --------------------------------------------------------------------------------------------------------------------
    # Configs
    # --------------------------------------------------------------------------------------------------------------------

    def make_config_file(
        self,
        local_path: str,
        remote_path: str,
        connection_method: str,
        remote_host_id: Optional[str] = None,
        remote_host_username: Optional[str] = None,
        use_ephys: bool = False,
        use_behav: bool = False,
        use_funcimg: bool = False,
        use_histology: bool = False,
    ) -> None:
        """
        Initialise the configurations for datashuttle to use on the
        local machine. Once initialised, these settings will be
        used each time the datashuttle is opened. This method
        can also be used to completely overwrite existing configs.

        These settings are stored in a config file on the
        datashuttle path (not in the project directory)
        on the local machine. Use get_config_path() to
        get the full path to the saved config file.

        Use update_config() to update a single config, and
        supply_config() to use an existing config file.

        Parameters
        ----------

        local_path :
            path to project dir on local machine

        remote_path :
            Filepath to remote project.
            If this is local (i.e. connection_method = "local_filesystem"),
            this is the full path on the local filesystem
            Otherwise, if this is via ssh (i.e. connection method = "ssh"),
            this is the path to the project directory on remote machine.
            This should be a full path to remote directory i.e. this cannot
            include ~ home directory syntax, must contain the full path
            (e.g. /nfs/nhome/live/jziminski)

        connection_method :
            The method used to connect to the remote project filesystem,
            e.g. "local_filesystem" (e.g. mounted drive) or "ssh"

        remote_host_id :
            server address for remote host for ssh connection
            e.g. "ssh.swc.ucl.ac.uk"

        remote_host_username :
            username for which to log in to remote host.
            e.g. "jziminski"

        use_ephys :
            if True, will allow ephys directory creation

        use_funcimg :
            if True, will allow funcimg directory creation

        use_histology :
            if True, will allow histology directory creation

        use_behav :
            if True, will allow behav directory creation
        """
        self._start_log(
            "make_config_file", store_in_temp_dir=True, temp_dir_path="default"
        )

        self.cfg = Configs(
            self._config_path,
            {
                "local_path": local_path,
                "remote_path": remote_path,
                "connection_method": connection_method,
                "remote_host_id": remote_host_id,
                "remote_host_username": remote_host_username,
                "use_ephys": use_ephys,
                "use_behav": use_behav,
                "use_funcimg": use_funcimg,
                "use_histology": use_histology,
            },
        )

        self.cfg.setup_after_load()  # will raise if fails

        if self.cfg:
            self.cfg.dump_to_file()

        self._set_attributes_after_config_load()

        self._setup_rclone_remote_local_filesystem_config()

        utils.log_and_message(
            "Configuration file has been saved and "
            "options loaded into datashuttle."
        )
        self._log_successful_config_change()
        self._move_logs_from_temp_dir()

    def update_config(
        self, option_key: str, new_info: Union[Path, str, bool, None]
    ) -> None:
        """
        Update a single config entry. This will overwrite the existing
        entry in the saved configs file and be used for all future
        datashuttle sessions.

        Parameters
        ----------

        option_key :
            dictionary key of the option to change,
            see make_config_file() for available keys.

        new_info :
            value to update the config too

        Notes
        -----
        If the local path is changed with update_config(),
        there are a couple of possibilities for where logs are stored.
        If the local_path project already exists, the config log will be
        written to the original local_path, and future logs will
        be written to the new local path. However, if a local_path does
        not exist, move to a temp_dir and then move the logs to the
        new local_path if successful.
        """
        store_logs_in_temp_dir = (
            option_key == "local_path" and not self._local_path_exists()
        )

        if store_logs_in_temp_dir:
            self._start_log(
                "update_config",
                store_in_temp_dir=True,
                temp_dir_path="default",
            )
        else:
            self._start_log("update_config", store_in_temp_dir=False)

        if not self.cfg:
            utils.log_and_raise_error(
                "Must have a config loaded before updating configs."
            )

        new_info = load_configs.handle_bool(option_key, new_info)

        self.cfg.update_an_entry(option_key, new_info)
        self._set_attributes_after_config_load()

        self._log_successful_config_change()

        if store_logs_in_temp_dir:
            self._move_logs_from_temp_dir()

    def supply_config_file(
        self, input_path_to_config: str, warn: bool = True
    ) -> None:
        """
        Supply an existing config by passing the path the config
        file (.yaml). The config file must contain exactly the
        same keys as the dataShuttle config, with
        values the same type, or will result in an error.

        If successful, the config will be loaded into datashuttle,
        and a copy saved in the DataShuttle config folder for future use.

        To check the format of a datashuttle config, one can be generated
        with make_config_file() or look in configs/canonical_configs.py.

        It is possible the local_path will be changed
        with the new config file. see update_config()
        for how this is handled.

        Parameters
        ----------

        input_path_to_config :
            Path to the config to use as DataShuttle config.

        warn :
            prompt the user to confirm as supplying
            config will overwrite existing config.
            Turned off for testing.
        """
        store_logs_in_temp_dir = not self._local_path_exists()
        if store_logs_in_temp_dir:
            self._start_log(
                "supply_config_file",
                store_in_temp_dir=True,
                temp_dir_path="default",
            )
        else:
            self._start_log("supply_config_file", store_in_temp_dir=False)

        path_to_config = Path(input_path_to_config)

        new_cfg = load_configs.supplied_configs_confirm_overwrite(
            path_to_config, warn
        )

        if new_cfg:
            self.cfg = new_cfg
            self._set_attributes_after_config_load()
            self.cfg.file_path = self._config_path
            self.cfg.dump_to_file()

            self._log_successful_config_change(message=True)
            if store_logs_in_temp_dir:
                self._move_logs_from_temp_dir()

    # --------------------------------------------------------------------------------------------------------------------
    # Public Getters
    # --------------------------------------------------------------------------------------------------------------------

    def get_local_path(self) -> None:
        """
        Print the projects local path.
        """
        utils.message_user(self.cfg["local_path"].as_posix())

    def get_datashuttle_path(self) -> None:
        """
        Print the path to the local datashuttle
        directory where configs another other
        datashuttle files are stored.
        """
        utils.message_user(self._datashuttle_path.as_posix())

    def get_config_path(self) -> None:
        """
        Print the full path to the DataShuttle config file.
        This is always formatted to UNIX style.
        """
        utils.message_user(self._config_path.as_posix())

    def get_remote_path(self) -> None:
        """
        Print the project remote path.
        This is always formatted to UNIX style.
        """
        utils.message_user(self.cfg["remote_path"].as_posix())

    def show_configs(self) -> None:
        """
        Print the current configs to the terminal.
        """
        utils.message_user(self._get_json_dumps_config())

    def show_local_tree(self):
        """
        Print a tree schematic of all files and directories
        in the local project.
        """
        ds_logger.print_tree(self.cfg["local_path"])

    @staticmethod
    def check_name_formatting(names: Union[str, list], prefix: str) -> None:
        """
        Pass list of names to check how these will be auto-formatted,
        for example as when passed to make_sub_dir() or upload_data() or
        download_data()

        Useful for checking tags e.g. @TO@, @DATE@, @DATETIME@, @DATE@.
        This method will print the formatted list of names,

        Parameters
        ----------

        names :
            A string or list of subject or session names.
        prefix:
            The relevant subject or session prefix,
            e.g. "sub-" or "ses-"
        """
        if prefix not in ["sub-", "ses-"]:
            utils.log_and_raise_error("prefix: must be 'sub-' or 'ses-'")

        formatted_names = formatting.format_names(names, prefix)
        utils.message_user(formatted_names)

    def make_and_get_logging_path(self) -> Path:
        """
        Currently logging is located in config path
        """
        logging_path = self._project_metadata_path / "logs"
        directories.make_dirs(logging_path)
        return logging_path

    # ====================================================================================================================
    # Private Functions
    # ====================================================================================================================

    # --------------------------------------------------------------------------------------------------------------------
    # Make Directory Trees
    # --------------------------------------------------------------------------------------------------------------------

    def _make_directory_trees(
        self,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        data_type: str,
        log: bool = False,
    ) -> None:
        """
        Entry method to make a full directory tree. It will
        iterate through all passed subjects, then sessions, then
        subdirs within a data_type directory. This
        permits flexible creation of directories (e.g.
        to make subject only, do not pass session name.

        Ensure sub and ses names are already formatted
        before use in this function (see _start_log())

        Parameters
        ----------

        sub_names, ses_names, data_type : see make_sub_dir()

        log : whether to log or not. If True, logging must
            already be initialised.
        """
        if data_type not in [[""], ""]:
            self._check_data_type_is_valid(data_type, error_on_fail=True)

        for sub in sub_names:

            sub_path = self._make_path(
                "local",
                [self._top_level_dir_name, sub],
            )

            directories.make_dirs(sub_path, log)

            self._make_data_type_directories(data_type, sub_path, "sub")

            for ses in ses_names:

                ses_path = self._make_path(
                    "local",
                    [self._top_level_dir_name, sub, ses],
                )

                directories.make_dirs(ses_path, log)

                self._make_data_type_directories(
                    data_type, ses_path, "ses", log=log
                )

    def _make_data_type_directories(
        self,
        data_type: Union[list, str],
        sub_or_ses_level_path: Path,
        level: str,
        log: bool = False,
    ) -> None:
        """
        Make data_type folder (e.g. behav) at the sub or ses
        level. Checks directory_class.Directories attributes,
        whether the data_type is used and at the current level.

        Parameters
        ----------
        data_type : data type (e.g. "behav", "all") to use. Use
            empty string ("") for none.

        sub_or_ses_level_path : Full path to the subject
            or session directory where the new directory
            will be written.

        level : The directory level that the
            directory will be made at, "sub" or "ses"

        log : whether to log on or not (if True, logging must
            already be initialised).
        """
        if data_type in [[""], ""]:
            return

        data_type_items = self._get_data_type_items(data_type)

        for data_type_key, data_type_dir in data_type_items:  # type: ignore

            if data_type_dir.used and data_type_dir.level == level:

                data_type_path = sub_or_ses_level_path / data_type_dir.name

                directories.make_dirs(data_type_path, log)

                directories.make_datashuttle_metadata_folder(
                    data_type_path, log
                )

    # --------------------------------------------------------------------------------------------------------------------
    # File Transfer
    # --------------------------------------------------------------------------------------------------------------------

    def _transfer_sub_ses_data(
        self,
        upload_or_download: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        data_type: str,
        dry_run: bool,
        log: bool = True,
    ) -> None:
        """
        Iterate through all data type, sub, ses and transfer directory.

        Parameters
        ----------

        upload_or_download : "upload" or "download"

        sub_names : see make_sub_dir()

        ses_names : see make_sub_dir()

        data_type : e.g. ephys, behav, histology, funcimg, see make_sub_dir()

        dry_run : see upload_project_dir_or_file()
        """
        local_or_remote = (
            "local" if upload_or_download == "upload" else "remote"
        )
        base_dir = self._get_base_and_top_level_dir(local_or_remote)

        # Find sub names to transfer
        if sub_names in ["all", ["all"]]:
            sub_names = directories.search_sub_or_ses_level(
                self,
                base_dir,
                local_or_remote,
                search_str=f"{self.cfg.sub_prefix}*",
            )
        else:
            sub_names = self._format_names(sub_names, "sub")
            sub_names = directories.search_for_wildcards(
                self, base_dir, local_or_remote, sub_names
            )

        for sub in sub_names:

            self._transfer_data_type(
                upload_or_download,
                local_or_remote,
                data_type,
                sub,
                dry_run=dry_run,
                log=log,
            )

            # Find ses names  to transfer
            if ses_names in ["all", ["all"]]:
                ses_names = directories.search_sub_or_ses_level(
                    self,
                    base_dir,
                    local_or_remote,
                    sub,
                    search_str=f"{self.cfg.ses_prefix}*",
                )
            else:
                ses_names = self._format_names(ses_names, "ses")
                ses_names = directories.search_for_wildcards(
                    self, base_dir, local_or_remote, ses_names, sub=sub
                )

            for ses in ses_names:

                self._transfer_data_type(
                    upload_or_download,
                    local_or_remote,
                    data_type,
                    sub,
                    ses,
                    dry_run=dry_run,
                    log=log,
                )

    def _transfer_data_type(
        self,
        upload_or_download: str,
        local_or_remote: str,
        data_type: Union[list, str],
        sub: str,
        ses: Optional[str] = None,
        dry_run: bool = False,
        log: bool = False,
    ) -> None:
        """
        Transfer the data_type-level folder at the subject
        or session level. data_type dirs are got either
        directly from user input or if "all" is passed searched
        for in the local / remote directory (for
        upload / download respectively).

        This can handle both cases of subject level dir (e.g. histology)
        or session level dir (e.g. ephys).

        Note that the use of upload_or_download / local_or_remote
        is redundant as the value of local_or_remote is set by
        upload_or_download, but kept for readability.

        Parameters
        ----------

        upload_or_download : "upload" or "download"

        local_or_remote : "local" or "remote"

        data_type : e.g. "behav", "all"

        sub : subject name

        ses : Optional session name. If False, directory
            to transfer will be assumed to be at the
            subject level.

        dry_run : Show data transfer output but do not
            actually transfer the data.

        log : Whether to log, if True logging must already
            be initialsied
        """
        level = "ses" if ses else "sub"

        data_type_items = self._items_from_data_type_input(
            local_or_remote, data_type, sub, ses
        )

        for data_type_key, data_type_dir in data_type_items:  # type: ignore

            if data_type_dir.level == level:
                if ses:
                    filepath = os.path.join(sub, ses, data_type_dir.name)
                else:
                    filepath = os.path.join(sub, data_type_dir.name)

                self._move_dir_or_file(
                    filepath,
                    upload_or_download,
                    dry_run=dry_run,
                    log=log,
                )

    def _move_dir_or_file(
        self,
        filepath: str,
        upload_or_download: str,
        dry_run: bool,
        log: bool = False,
    ) -> None:
        """
        Low-level function to transfer a directory or file.

        Parameters
        ----------

        filepath : filepath (not including local
            or remote root) to copy

        upload_or_download : "upload" or "download".
            upload goes local to remote, download goes
            remote to local

        dry_run : do not actually move the files,
            just report what would be moved.
        """
        local_filepath = self._make_path(
            "local", [self._top_level_dir_name, filepath]
        ).as_posix()

        remote_filepath = self._make_path(
            "remote", [self._top_level_dir_name, filepath]
        ).as_posix()

        output = rclone.transfer_data(
            local_filepath,
            remote_filepath,
            self._get_rclone_config_name(),
            upload_or_download,
            dry_run,
        )

        if log:
            utils.log(output.stderr.decode("utf-8"))
        utils.message_user(output.stderr.decode("utf-8"))

    def _items_from_data_type_input(
        self,
        local_or_remote: str,
        data_type: Union[list, str],
        sub: str,
        ses: Optional[str] = None,
    ) -> Union[ItemsView, zip]:
        """
        Get the list of data_types to transfer, either
        directly from user input, or by searching
        what is available if "all" is passed.

        Parameters
        ----------

        see _transfer_data_type() for parameters.
        """
        base_dir = self._get_base_and_top_level_dir(local_or_remote)

        if data_type not in ["all", ["all"]]:
            data_type_items = self._get_data_type_items(
                data_type,
            )
        else:
            data_type_items = directories.search_data_dirs_sub_or_ses_level(
                self,
                self._data_type_dirs,
                base_dir,
                local_or_remote,
                sub,
                ses,
            )

        return data_type_items

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    def _setup_ssh_key_and_rclone_config(self, log: bool = True) -> None:
        """
        Setup ssh connection, key pair (see ssh.setup_ssh_key)
        for details. Also setup rclone config for ssh connection.
        """
        ssh.setup_ssh_key(
            self._ssh_key_path, self._hostkeys_path, self.cfg, log=log
        )

        self._setup_rclone_remote_ssh_config(log)

    # --------------------------------------------------------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------------------------------------------------------

    def _make_path(self, base: str, subdirs: Union[str, list]) -> Path:
        """
        Function for joining relative path to base dir.
        If path already starts with base dir, the base
        dir will not be joined.

        Parameters
        ----------

        base: "local", "remote" or "datashuttle"

        subdirs: a list (or string for 1) of
            directory names to be joined into a path.
            If file included, must be last entry (with ext).
        """
        if isinstance(subdirs, list):
            subdirs_str = "/".join(subdirs)
        else:
            subdirs_str = cast(str, subdirs)

        subdirs_path = Path(subdirs_str)

        base_dir = self._get_base_dir(base)

        if utils.path_already_stars_with_base_dir(base_dir, subdirs_path):
            joined_path = subdirs_path
        else:
            joined_path = base_dir / subdirs_path

        return joined_path

    def _get_base_dir(self, base: str) -> Path:
        """
        Convenience function to return the full base path.

        Parameters
        ----------

        base : base path, "local", "remote" or "datashuttle"

        """
        if base == "local":
            base_dir = self.cfg["local_path"]
        elif base == "remote":
            base_dir = self.cfg["remote_path"]
        elif base == "datashuttle":
            base_dir, __ = utils.get_datashuttle_path(self.project_name)
        return base_dir

    def _get_base_and_top_level_dir(self, local_or_remote: str) -> Path:
        """
        Get the base project directory with the top level directory,
        i.e. "rawdata" or "derivatives".

        Parameters
        ----------

        local_or_remote : "local" or "remote"

        Examples
        --------
        e.g. if local_path = "/my/local/path and the
        top level directory is set to rawdata, this method will return
        "/my/local/path/rawdata"
        """
        base_dir = (
            self._get_base_dir(local_or_remote) / self._top_level_dir_name
        )
        return base_dir

    def _format_names(
        self, names: Union[list, str], sub_or_ses: str
    ) -> List[str]:
        """
        Format a list of subject or session names, e.g.
        by ensuring all have sub- or ses- prefix, checking
        for tags, that names do not include spaces and that
        there are not duplicates.

        Parameters
        ----------

        names: str or list containing sub or ses names
                      (e.g. to make dirs)

        sub_or_ses: "sub" or "ses" - this defines the prefix checks.
        """
        prefix = self._get_sub_or_ses_prefix(sub_or_ses)
        formatted_names = formatting.format_names(names, prefix)

        return formatted_names

    def _get_sub_or_ses_prefix(self, sub_or_ses: str) -> str:
        """
        Get the sub / ses prefix (default is "sub-" and "ses-") set in cfgs.
        These should always be "sub-" or "ses-" by SWC-BIDS.
        """
        if sub_or_ses == "sub":
            prefix = self.cfg.sub_prefix
        elif sub_or_ses == "ses":
            prefix = self.cfg.ses_prefix
        return prefix

    def _check_data_type_is_valid(
        self, data_type: str, error_on_fail: bool
    ) -> bool:
        """
        Check the passed data_type is valid (must
        be a key on self.ses_dirs e.g. "behav", or "all")
        """
        if type(data_type) == list:
            valid_keys = list(self._data_type_dirs.keys()) + ["all"]
            is_valid = all([type in valid_keys for type in data_type])
        else:
            is_valid = (
                data_type in self._data_type_dirs.keys() or data_type == "all"
            )

        if error_on_fail and not is_valid:
            utils.log_and_raise_error(
                f"data_type: '{data_type}' "
                f"is not valid. Must be one of"
                f" {list(self._data_type_dirs.keys())}. or 'all'"
                f" No directories were made."
            )

        return is_valid

    def _get_data_type_items(
        self, data_type: Union[str, list]
    ) -> Union[ItemsView, zip]:
        """
        Get the .items() structure of the data type, either all of
        them (stored in self._data_type_dirs) or as a single item.
        """
        if type(data_type) == str:
            data_type = [data_type]

        if "all" in data_type:
            items = self._data_type_dirs.items()
        else:
            items = zip(
                data_type,
                [self._data_type_dirs[key] for key in data_type],
            )

        return items

    def _get_rclone_config_name(
        self, connection_method: Optional[str] = None
    ) -> str:
        """
        Convenience function to get the rclone config
        name (these configs are created by datashuttle
        but managed and stored by rclone).
        """
        if connection_method is None:
            connection_method = self.cfg["connection_method"]

        return f"remote_{self.project_name}_{connection_method}"

    def _start_log(
        self,
        name: str,
        variables: Optional[List[Any]] = None,
        store_in_temp_dir: bool = False,
        temp_dir_path: Union[str, Path] = "",
    ) -> None:
        """
        Initialize the logger. This is typically called at
        the start of public methods to initialize logging
        for a specific function call.

        Parameters
        ----------

        name : name of the log output files. Typically, the
            name of the function logged e.g. "update_config"

        variables : variables are passed to fancylog variables argument.

        store_in_temp_dir :
            if False, existing logging path will be used
            (local project .datashuttle). If "default"", the temp
            log backup will be used. Otherwise, expect a path / string
            to the new path to make the logs at.

        temp_dir_path :
            if "default", use the default temp dir path stored at
            self._temp_log_path otherwise a full path to save the log at.
        """
        if store_in_temp_dir:
            path_to_save = (
                self._temp_log_path
                if temp_dir_path == "default"
                else Path(temp_dir_path)
            )
        else:
            path_to_save = self._logging_path

        ds_logger.start(path_to_save, name, variables)

    def _move_logs_from_temp_dir(self):
        """
        Logs are stored within the project directory. Although
        in some instances, when setting configs, we do not know what
        the project directory is. In this case, make the logs
        in a temp folder in the .datashuttle config dir,
        and move them to the project folder once set.
        """
        if not self.cfg or not self.cfg["local_path"].is_dir():
            utils.log_and_raise_error(
                "Project folder does not exist. Logs were not moved."
            )

        ds_logger.close_log_filehandler()

        log_files = glob.glob(str(self._temp_log_path / "*.log"))
        for file_path in log_files:
            file_name = os.path.basename(file_path)

            shutil.move(
                self._temp_log_path / file_name, self._logging_path / file_name
            )

    def _log_successful_config_change(self, message=False):
        """
        Log the entire config at the time of config change.
        If messaged, just message "update successful" rather than
        print the entire configs as it becomes confusing.
        """
        if message:
            utils.message_user("Update successful.")
        utils.log(
            f"Update successful. New config file: \n {self._get_json_dumps_config()}"
        )

    def _get_json_dumps_config(self):
        """
        Get the config dictionary formatted as json.dumps()
        which allows well formatted printing.
        """
        copy_dict = copy.deepcopy(self.cfg.data)
        self.cfg.convert_str_and_pathlib_paths(copy_dict, "path_to_str")
        return json.dumps(copy_dict, indent=4)

    def _local_path_exists(self):
        """
        Check the local_path for the project exists.
        """
        return self.cfg and self.cfg["local_path"].is_dir()

    def _make_project_metadata_if_does_not_exist(self):
        """
        Within the project local_path is also a .datashuttle
        folder that contains additional information, e.g. logs.
        """
        directories.make_dirs(self._project_metadata_path, log=False)

    def _setup_rclone_remote_ssh_config(self, log):
        rclone.setup_remote_as_rclone_target(
            "ssh",
            self.cfg,
            self._get_rclone_config_name("ssh"),
            self._ssh_key_path,
            log=log,
        )

    def _setup_rclone_remote_local_filesystem_config(self):
        rclone.setup_remote_as_rclone_target(
            "local_filesystem",
            self.cfg,
            self._get_rclone_config_name("local_filesystem"),
            self._ssh_key_path,
            log=True,
        )
