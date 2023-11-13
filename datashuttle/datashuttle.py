from __future__ import annotations

import copy
import glob
import json
import os
import shutil
import warnings
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import paramiko
import yaml

from datashuttle.configs import canonical_folders, load_configs
from datashuttle.configs.config_class import Configs
from datashuttle.utils import (
    ds_logger,
    folders,
    formatting,
    getters,
    rclone,
    ssh,
    utils,
    validation,
)
from datashuttle.utils.custom_exceptions import (
    ConfigError,
    NeuroBlueprintError,
)
from datashuttle.utils.data_transfer import TransferData
from datashuttle.utils.decorators import (  # noqa
    check_configs_set,
    requires_ssh_configs,
)

# -----------------------------------------------------------------------------
# Project Manager Class
# -----------------------------------------------------------------------------


class DataShuttle:
    """
    DataShuttle is a tool for convenient scientific
    project management and data transfer in BIDS format.

    The expected organisation is a central repository
    on a central machine  ('central') that contains all
    project data. This is connected to multiple local
    machines ('local'). These can each contain a subset of
    the full project (e.g. machine for electrophysiology
    collection, machine for behavioural collection).

    On first use on a new profile, show warning prompting
    to set configurations with the function make_config_file().

    Datashuttle will save logs to a .datashuttle folder
    in the main local project. These logs contain
    detailed information on folder creation / transfer.
    To get the path to datashuttle logs, use
    cfgs.make_and_get_logging_path().

    For transferring data between a central data storage
    with SSH, use setup setup_ssh_connection_to_central_server().
    This will allow you to check the server key, add host key to
    profile if accepted, and setup ssh key pair.

    Parameters
    ----------

    project_name : The project name to use the datashuttle
                   Folders containing all project files
                   and folders are specified in make_config_file().
                   Datashuttle-related files are stored in
                   a .datashuttle folder in the user home
                   folder. Use show_datashuttle_path() to
                   see the path to this folder.

    print_startup_message : If `True`, a start-up message displaying the
                            current state of the program (e.g. persistent
                            settings such as the 'top-level folder') is shown.
    """

    def __init__(self, project_name: str, print_startup_message: bool = True):
        if " " in project_name:
            utils.log_and_raise_error(
                "'project_name' must not include spaces.", ValueError
            )

        self.project_name = project_name
        (
            self._datashuttle_path,
            self._temp_log_path,
        ) = canonical_folders.get_project_datashuttle_path(self.project_name)

        self._config_path = self._datashuttle_path / "config.yaml"

        self._persistent_settings_path = (
            self._datashuttle_path / "persistent_settings.yaml"
        )
        self.cfg: Any = None

        self.cfg = load_configs.make_config_file_attempt_load(
            self.project_name, self._config_path
        )

        if self.cfg:
            self._set_attributes_after_config_load()

        if print_startup_message:
            if self.cfg:
                self.show_top_level_folder()

        rclone.prompt_rclone_download_if_does_not_exist()

    def _set_attributes_after_config_load(self) -> None:
        """
        Once config file is loaded, update all private attributes
        according to config contents.
        """
        self.cfg.top_level_folder = self._load_persistent_settings()[
            "top_level_folder"
        ]

        self.cfg.init_paths()

        self._make_project_metadata_if_does_not_exist()

    # -------------------------------------------------------------------------
    # Public Folder Makers
    # -------------------------------------------------------------------------

    @check_configs_set
    def set_top_level_folder(self, folder_name: str) -> None:
        """
        Set the working top level folder (e.g. 'rawdata', 'derivatives').

        The top_level_folder defines in which top level folder new
        sub-folders will be made (e.g. make_folders) or at which level
        folders  are transferred with the commands upload / download
        and upload_all / download all.

        To upload the entire project (i.e. every top level
        folder), use the 'command upload_entire_project' or
        'download_entire_project'.
        """
        canonical_top_level_folders = canonical_folders.get_top_level_folders()

        if folder_name not in canonical_top_level_folders:
            utils.raise_error(
                f"Folder name: {folder_name} "
                f"is not in permitted top-level folder"
                f" names: {canonical_top_level_folders}",
                ValueError,
            )

        self.cfg.top_level_folder = folder_name

        self._update_persistent_setting("top_level_folder", folder_name)

        self.show_top_level_folder()

    @check_configs_set
    def make_folders(
        self,
        sub_names: Union[str, List[str]],
        ses_names: Optional[Union[str, List[str]]] = None,
        datatype: str = "",
    ) -> None:
        """
        Create a subject / session folder tree in the project
        folder.

        Parameters
        ----------

        sub_names :
                subject name / list of subject names to make
                within the top-level project folder
                (if not already, these will be prefixed with
                "sub-")
        ses_names :
                (Optional). session name / list of session names.
                (if not already, these will be prefixed with
                "ses-"). If no session is provided, no session-level
                folders are made.
        datatype :
                The datatype to make in the sub / ses folders.
                (e.g. "ephys", "behav", "anat"). If "all"
                is selected, all datatypes permitted in
                NeuroBlueprint will be created. If "" is passed
                no datatype will be created.

        Notes
        -----

        sub_names or ses_names may contain formatting tags

            @TO@ :
                used to make a range of subjects / sessions.
                Boundaries of the range must be either side of the tag
                e.g. sub-001@TO@003 will generate
                 ["sub-001", "sub-002", "sub-003"]

            @DATE@, @TIME@ @DATETIME@ :
                will add date-<value>, time-<value> or
                date-<value>_time-<value> keys respectively. Only one per-name
                is permitted.
                e.g. sub-001_@DATE@ will generate sub-001_date-20220101
                (on the 1st january, 2022).

        Examples
        --------
        project.make_folders("sub-001", datatype="all")

        project.make_folders("sub-002@TO@005",
                             ["ses-001", "ses-002"],
                             ["ephys", "behav"])
        """
        self._start_log("make-folders", local_vars=locals())

        self.show_top_level_folder()

        utils.log("\nFormatting Names...")
        ds_logger.log_names(["sub_names", "ses_names"], [sub_names, ses_names])

        sub_names = formatting.check_and_format_names(sub_names, "sub")

        if ses_names is not None:
            ses_names = formatting.check_and_format_names(ses_names, "ses")
        else:
            ses_names = []

        ds_logger.log_names(
            ["formatted_sub_names", "formatted_ses_names"],
            [sub_names, ses_names],
        )

        validation.validate_names_against_project(
            self.cfg,
            sub_names,
            ses_names,
            local_only=True,
            error_or_warn="error",
        )

        utils.log("\nMaking folders...")
        folders.make_folder_trees(
            self.cfg,
            sub_names,
            ses_names,
            datatype,
            log=True,
        )

        utils.log("\nFinished file creation. Local folder tree is now:\n")
        ds_logger.log_tree(self.cfg["local_path"])

        utils.print_message_to_user(
            f"Finished making folders. \nFor log of all created "
            f"folders, please see {self.cfg.logging_path}"
        )

        ds_logger.close_log_filehandler()

    @check_configs_set
    def get_next_sub_number(
        self, return_with_prefix: bool = True, local_only: bool = False
    ) -> str:
        """
        Convenience function for get_next_sub_or_ses_number
        to find the next subject number.

        Parameters
        ----------

        return_with_prefix : bool
            If `True`, return with the "sub-" prefix.

        local_only : bool
            If `True, only get names from `local_path`, otherwise from
            `local_path` and `central_path`.
        """
        return getters.get_next_sub_or_ses_number(
            self.cfg,
            sub=None,
            local_only=local_only,
            return_with_prefix=return_with_prefix,
            search_str="sub-*",
        )

    @check_configs_set
    def get_next_ses_number(
        self,
        sub: str,
        return_with_prefix: bool = True,
        local_only: bool = False,
    ) -> str:
        """
        Convenience function for get_next_sub_or_ses_number
        to find the next session number.

        Parameters
        ----------

        sub: Optional[str]
            Name of the subject to find the next session of.

        return_with_prefix : bool
            If `True`, return with the "ses-" prefix.

        local_only : bool
            If `True, only get names from `local_path`, otherwise from
            `local_path` and `central_path`.
        """
        return getters.get_next_sub_or_ses_number(
            self.cfg,
            sub=sub,
            local_only=local_only,
            return_with_prefix=return_with_prefix,
            search_str="ses-*",
        )

    # -------------------------------------------------------------------------
    # Public File Transfer
    # -------------------------------------------------------------------------

    @check_configs_set
    def upload(
        self,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        datatype: Union[List[str], str] = "all",
        dry_run: bool = False,
        init_log: bool = True,
    ) -> None:
        """
        Upload data from a local project to the central project
        folder. In the case that a file / folder exists on
        the central and local, the central will not be overwritten
        even if the central file is an older version. Data
        transfer logs are saved to the logging folder).

        Parameters
        ----------

        sub_names :
            a subject name / list of subject names. These must
            be prefixed with "sub-", or the prefix will be
            automatically added. "@*@" can be used as a wildcard.
            "all" will search for all sub-folders in the
            datatype folder to upload.
        ses_names :
            a session name / list of session names, similar to
            sub_names but requiring a "ses-" prefix.
        dry_run :
            perform a dry-run of upload. This will output as if file
            transfer was taking place, but no files will be moved. Useful
            to check which files will be moved on data transfer.
        datatype :
            see make_folders()

        init_log :
            (Optional). Whether to start the logger. This should
            always be True, unless logger has already been started
            (e.g. in a calling function).

        Notes
        -----

        The configs "overwrite_old_files", "transfer_verbosity"
        and "show_transfer_progress" pertain to data-transfer settings.
        See make_config_file() for more information.

        sub_names or ses_names may contain certain formatting tags:

        @*@: wildcard search for subject names. e.g. ses-001_date-@*@
             will transfer all session 001 collected on all dates.
        @TO@: used to transfer a range of sub/ses.
              Number must be either side of the tag
              e.g. sub-001@TO@003 will generate
              ["sub-001", "sub-002", "sub-003"]
        @DATE@, @TIME@ @DATETIME@: will add date-<value>, time-<value> or
              date-<value>_time-<value> keys respectively. Only one per-name
              is permitted.
              e.g. sub-001_@DATE@ will generate sub-001_date-20220101
              (on the 1st january, 2022).
        """
        if init_log:
            self._start_log("upload", local_vars=locals())

        self.show_top_level_folder()

        TransferData(
            self.cfg,
            "upload",
            sub_names,
            ses_names,
            datatype,
            dry_run,
            log=True,
        )
        ds_logger.close_log_filehandler()

    @check_configs_set
    def download(
        self,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        datatype: Union[List[str], str] = "all",
        dry_run: bool = False,
        init_log: bool = True,
    ) -> None:
        """
        Download data from the central project folder to the
        local project folder. In the case that a file / folder
        exists on the central and local, the local will
        not be overwritten even if the central file is an
        older version.

        This function is identical to upload() but with the direction
        of data transfer reversed. Please see upload() for arguments.
        "all" arguments will search the central
        project for sub / ses to download.
        """
        if init_log:
            self._start_log("download", local_vars=locals())

        self.show_top_level_folder()

        TransferData(
            self.cfg,
            "download",
            sub_names,
            ses_names,
            datatype,
            dry_run,
            log=True,
        )
        ds_logger.close_log_filehandler()

    @check_configs_set
    def upload_all(self, dry_run: bool = False) -> None:
        """
        Convenience function to upload all data.

        Alias for:
            project.upload("all", "all", "all")
        """
        self._start_log("upload-all", local_vars=locals())

        self.upload("all", "all", "all", dry_run=dry_run, init_log=False)

    @check_configs_set
    def download_all(self, dry_run: bool = False) -> None:
        """
        Convenience function to download all data.

        Alias for : project.download("all", "all", "all")
        """
        self._start_log("download-all", local_vars=locals())

        self.download("all", "all", "all", dry_run=dry_run, init_log=False)

    @check_configs_set
    def upload_entire_project(self) -> None:
        """
        Upload the entire project (from 'local' to 'central'),
        i.e. including every top level folder (e.g. 'rawdata',
        'derivatives', 'code', 'analysis').
        """
        self._transfer_entire_project("upload")

    @check_configs_set
    def download_entire_project(self) -> None:
        """
        Download the entire project (from 'central' to 'local'),
        i.e. including every top level folder (e.g. 'rawdata',
        'derivatives', 'code', 'analysis').
        """
        self._transfer_entire_project("download")

    @check_configs_set
    def upload_specific_folder_or_file(
        self, filepath: str, dry_run: bool = False
    ) -> None:
        """
        Upload a specific file or folder. If transferring
        a single file, the path including the filename is
        required (see 'filepath' input). If a folder,
        wildcards "*" or "**" must be used to transfer
        all files in the folder ("*") or all files
        and sub-folders ("**").

        e.g. "sub-001/ses-002/my_folder/**"

        This function works by passing the file / folder
        path to transfer to Rclone's --include flag.

        Parameters
        ----------

        filepath :
            a string containing the filepath to move,
            relative to the project folder "rawdata"
            or "derivatives" path (depending on which is currently
            set). Alternatively, the entire path is accepted.
        dry_run :
            perform a dry-run of upload. This will output as if file
            transfer was taking place, but no files will be moved. Useful
            to check which files will be moved on data transfer.
        """
        self._start_log("upload-specific-folder-or-file", local_vars=locals())

        self.show_top_level_folder()

        processed_filepath = utils.get_path_after_base_folder(
            self.cfg.get_base_folder("local"),
            Path(filepath),
        )

        include_list = [f"--include {processed_filepath.as_posix()}"]
        output = rclone.transfer_data(
            self.cfg,
            "upload",
            include_list,
            self.cfg.make_rclone_transfer_options(dry_run),
        )

        utils.log(output.stderr.decode("utf-8"))

        ds_logger.close_log_filehandler()

    @check_configs_set
    def download_specific_folder_or_file(
        self, filepath: str, dry_run: bool = False
    ) -> None:
        """
        Download a specific file or folder. If transferring
        a single file, the path including the filename is
        required (see 'filepath' input). If a folder,
        wildcards "*" or "**" must be used to transfer
        all files in the folder ("*") or all files
        and sub-folders ("**").

        e.g. "sub-001/ses-002/my_folder/**"

        This function works by passing the file / folder
        path to transfer to Rclone's --include flag.

        Parameters
        ----------

        filepath :
            a string containing the filepath to move,
            relative to the project folder "rawdata"
            or "derivatives" path (depending on which is currently
            set). Alternatively, the entire path is accepted.
        dry_run :
            perform a dry-run of upload. This will output as if file
            transfer was taking place, but no files will be moved. Useful
            to check which files will be moved on data transfer.
        """
        self._start_log(
            "download-specific-folder-or-file", local_vars=locals()
        )

        self.show_top_level_folder()

        processed_filepath = utils.get_path_after_base_folder(
            self.cfg.get_base_folder("central"),
            Path(filepath),
        )

        include_list = [f"--include /{processed_filepath.as_posix()}"]
        output = rclone.transfer_data(
            self.cfg,
            "download",
            include_list,
            self.cfg.make_rclone_transfer_options(dry_run),
        )

        utils.log(output.stderr.decode("utf-8"))

        ds_logger.close_log_filehandler()

    # -------------------------------------------------------------------------
    # SSH
    # -------------------------------------------------------------------------

    @requires_ssh_configs
    def setup_ssh_connection_to_central_server(self) -> None:
        """
        Setup a connection to the central server using SSH.
        Assumes the central_host_id and central_host_username
        are set in configs (see make_config_file() and update_config_file())

        First, the server key will be displayed, requiring
        verification of the server ID. This will store the
        hostkey for all future use.

        Next, prompt to input their password for the central
        cluster. Once input, SSH private / public key pair
        will be setup.
        """
        self._start_log(
            "setup-ssh-connection-to-central-server", local_vars=locals()
        )

        verified = ssh.verify_ssh_central_host(
            self.cfg["central_host_id"],
            self.cfg.hostkeys_path,
            log=True,
        )

        if verified:
            self._setup_ssh_key_and_rclone_config(log=True)

        ds_logger.close_log_filehandler()

    @requires_ssh_configs
    def write_public_key(self, filepath: str) -> None:
        """
        By default, the SSH private key only is stored, in
        the datashuttle configs folder. Use this function
        to save the public key.

        Parameters
        ----------

        filepath :
            full filepath (inc filename) to write the
            public key to.
        """
        key: paramiko.RSAKey
        key = paramiko.RSAKey.from_private_key_file(
            self.cfg.ssh_key_path.as_posix()
        )

        with open(filepath, "w") as public:
            public.write(key.get_base64())
        public.close()

    # -------------------------------------------------------------------------
    # Configs
    # -------------------------------------------------------------------------

    def make_config_file(
        self,
        local_path: str,
        central_path: str,
        connection_method: str,
        central_host_id: Optional[str] = None,
        central_host_username: Optional[str] = None,
        overwrite_old_files: bool = False,
        transfer_verbosity: str = "v",
        show_transfer_progress: bool = False,
    ) -> None:
        """
        Initialise the configurations for datashuttle to use on the
        local machine. Once initialised, these settings will be
        used each time the datashuttle is opened. This method
        can also be used to completely overwrite existing configs.

        These settings are stored in a config file on the
        datashuttle path (not in the project folder)
        on the local machine. Use show_config_path() to
        get the full path to the saved config file.

        Use update_config_file() to update a single config, and
        supply_config() to use an existing config file.

        Parameters
        ----------

        local_path :
            path to project folder on local machine

        central_path :
            Filepath to central project.
            If this is local (i.e. connection_method = "local_filesystem"),
            this is the full path on the local filesystem
            Otherwise, if this is via ssh (i.e. connection method = "ssh"),
            this is the path to the project folder on central machine.
            This should be a full path to central folder i.e. this cannot
            include ~ home folder syntax, must contain the full path
            (e.g. /nfs/nhome/live/jziminski)

        connection_method :
            The method used to connect to the central project filesystem,
            e.g. "local_filesystem" (e.g. mounted drive) or "ssh"

        central_host_id :
            server address for central host for ssh connection
            e.g. "ssh.swc.ucl.ac.uk"

        central_host_username :
            username for which to log in to central host.
            e.g. "jziminski"

        overwrite_old_files :
            If True, when copying data (upload or download) files
            will be overwritten if the timestamp of the copied
            version is later than the target folder version
            of the file i.e. edits made to a file in the source
            machine will be copied to the target machine. If False,
            a file will be copied if it does not exist on the target
            folder, otherwise it will never be copied, even if
            the source version of the file has a later timestamp.

        transfer_verbosity :
            "v" will tell you about each file that is transferred and
            significant events, "vv" will be very verbose and inform
            on all events.

        show_transfer_progress :
            If true, the real-time progress of file transfers will be printed.
        """
        self._start_log(
            "make-config-file",
            local_vars=locals(),
            store_in_temp_folder=True,
        )

        if self._config_path.is_file():
            warnings.warn(
                "A config file already exists. This function will completely"
                "overwrite the existing config file, and any arguments not"
                "passed to `make-config-file` will be set to the function "
                "defaults. "
                "Use `update-config-file` to selectively update settings."
            )

        self.cfg = Configs(
            self.project_name,
            self._config_path,
            {
                "local_path": local_path,
                "central_path": central_path,
                "connection_method": connection_method,
                "central_host_id": central_host_id,
                "central_host_username": central_host_username,
                "overwrite_old_files": overwrite_old_files,
                "transfer_verbosity": transfer_verbosity,
                "show_transfer_progress": show_transfer_progress,
            },
        )

        self.cfg.setup_after_load()  # will raise error if fails

        if self.cfg:
            self.cfg.dump_to_file()

        self._set_attributes_after_config_load()

        self._setup_rclone_central_local_filesystem_config()

        utils.log_and_message(
            "Configuration file has been saved and "
            "options loaded into datashuttle."
        )
        self._log_successful_config_change()
        self._move_logs_from_temp_folder()

        ds_logger.close_log_filehandler()

    def update_config_file(self, **kwargs) -> None:
        """ """
        if not self.cfg:
            utils.log_and_raise_error(
                "Must have a config loaded before updating configs."
            )

        self._start_log(
            "update-config-file",
            local_vars=locals(),
        )

        for option, value in kwargs.items():
            if option in self.cfg.keys_str_on_file_but_path_in_class:
                kwargs[option] = Path(value)

        new_cfg = copy.deepcopy(self.cfg)
        new_cfg.update(**kwargs)

        check_change = new_cfg.safe_check_current_dict_is_valid()

        if check_change["passed"]:
            self.cfg = new_cfg
            self._set_attributes_after_config_load()
            self.cfg.dump_to_file()
            self._log_successful_config_change(message=True)
            ds_logger.close_log_filehandler()
        else:
            utils.log_and_raise_error(
                f"{check_change['error']}\nConfigs were not updated.",
                ConfigError,
            )

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

        Logs are stored in a temporary folder and then moved to the
        new local path provided in the supplied configs.

        Parameters
        ----------

        input_path_to_config :
            Path to the config to use as DataShuttle config.

        warn :
            prompt the user to confirm as supplying
            config will overwrite existing config.
            Turned off for testing.
        """
        self._start_log(
            "supply-config-file",
            local_vars=locals(),
            store_in_temp_folder=True,
        )

        path_to_config = Path(input_path_to_config)

        new_cfg = load_configs.supplied_configs_confirm_overwrite(
            self.project_name, path_to_config, warn
        )

        if new_cfg:
            self.cfg = new_cfg
            self._set_attributes_after_config_load()
            self.cfg.file_path = self._config_path
            self.cfg.dump_to_file()

            self._log_successful_config_change(message=True)
            self._move_logs_from_temp_folder()
        ds_logger.close_log_filehandler()

    # -------------------------------------------------------------------------
    # Public Getters
    # -------------------------------------------------------------------------

    @check_configs_set
    def show_local_path(self) -> None:
        """
        Print the projects local path.
        """
        utils.print_message_to_user(self.cfg["local_path"].as_posix())

    def show_datashuttle_path(self) -> None:
        """
        Print the path to the local datashuttle
        folder where configs another other
        datashuttle files are stored.
        """
        utils.print_message_to_user(self._datashuttle_path.as_posix())

    @check_configs_set
    def show_config_path(self) -> None:
        """
        Print the full path to the DataShuttle config file.
        This is always formatted to UNIX style.
        """
        utils.print_message_to_user(self._config_path.as_posix())

    @check_configs_set
    def show_central_path(self) -> None:
        """
        Print the project central path.
        This is always formatted to UNIX style.
        """
        utils.print_message_to_user(self.cfg["central_path"].as_posix())

    @check_configs_set
    def show_configs(self) -> None:
        """
        Print the current configs to the terminal.
        """
        utils.print_message_to_user(self._get_json_dumps_config())

    @check_configs_set
    def show_logging_path(self) -> None:
        """
        Print the path where datashuttle logs are written.
        """
        utils.print_message_to_user(self.cfg.logging_path)

    @check_configs_set
    def show_local_tree(self) -> None:
        """
        Print a tree schematic of all files and folders
        in the local project.
        """
        ds_logger.print_tree(self.cfg["local_path"])

    @check_configs_set
    def show_top_level_folder(self) -> None:
        """
        Print the current working top level folder (e.g.
        'rawdata', 'derivatives')

        The top_level_folder defines in which top level folder new
        sub-folders will be made (e.g. make_folders) or
        at which level folders are transferred with the commands
        upload / download and upload_all / download all.
        upload_specific_folder_or_file / download_specific_folder_or_file.

        To upload the entire project (i.e. every top level
        folder), use the 'command upload_entire_project' or
        'download_entire_project'.
        """
        utils.print_message_to_user(
            f"\nThe working top level folder is: "
            f"{self.cfg.top_level_folder}\n"
        )

    @check_configs_set
    def show_next_sub_number(self) -> None:
        """
        Show a suggested value for the next available subject number.
        The local and central repository will be searched, and the
        maximum existing subject number + 1 will be suggested.

        In the case where there are multiple 'local' machines interacting
        with a central central repository, this function will not detect
        subject numbers of other 'local' machines. For example, if there
        is one machine for behavioural and another for electrophysiological
        data collection, connected to a central server that is 'central'.
        If run on the behavioural data collection machine, this function
        will suggest the next number based on the subjects found on the
        behavioural machine and central machine, but not the
        electrophysiological machine.
        """
        suggested_new_num = self.get_next_sub_number()

        utils.print_message_to_user(
            "Local and Central repository searched. "
            f"The suggested new subject number is: {suggested_new_num}"
        )

    @check_configs_set
    def show_next_ses_number(self, sub: Optional[str]) -> None:
        """
        Show a suggested value for the next session number of a
        given subject. The local and central repository will be
        searched, and the maximum session number + 1 will be suggested.

        In the case where there are multiple 'local' machines interacting
        with a central repository, this function will not detect
        session numbers of other 'local' machines. For example, if there
        is one machine for behavioural and another for electrophysiological
        data collection, connected to a central server that is 'central'.
        If run on the behavioural data collection machine, this function
        will suggest the next number based on the sessions found on the
        behavioural machine and central machine, but not the
        electrophysiological machine.

        Parameters
        ----------

        sub : the subject for which to suggest the next available session.
        """
        suggested_new_num = self.get_next_ses_number(sub)

        utils.print_message_to_user(
            f"Local and Central repository searched for sessions for {sub}. "
            f"The suggested new session number is: {suggested_new_num}"
        )

    def show_existing_projects(self) -> None:
        """
        Print a list of existing project names found on the local machine.
        This is based on project folders in the "home / .datashuttle" folder
        that contain valid config.yaml files.
        """
        project_names, _ = getters.get_existing_project_paths_and_names()
        utils.print_message_to_user(
            f"The existing project names are {project_names}."
        )

    @check_configs_set
    def validate_project(
        self, error_or_warn: Literal["error", "warn"], local_only: bool = False
    ) -> None:
        """
        Perform validation on the project. Currently checks that
        sub and ses values have the same length for all sub and
        ses in the project.
        """
        self._start_log(
            "validate-project",
            local_vars=locals(),
        )

        validation.validate_project(
            self.cfg, local_only=local_only, error_or_warn=error_or_warn
        )

        ds_logger.close_log_filehandler()

    @staticmethod
    def check_name_formatting(
        names: Union[str, list], prefix: Literal["sub", "ses"]
    ) -> None:
        """
        Pass list of names to check how these will be auto-formatted,
        for example as when passed to make_folders() or upload()
        or download()

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
        if prefix not in ["sub", "ses"]:
            utils.log_and_raise_error(
                "'prefix' must be 'sub' or 'ses'.",
                NeuroBlueprintError,
            )

        if isinstance(names, str):
            names = [names]

        formatted_names = formatting.format_names(names, prefix)
        utils.print_message_to_user(formatted_names)

    # -------------------------------------------------------------------------
    # Private Functions
    # -------------------------------------------------------------------------

    def _transfer_entire_project(
        self, direction: Literal["upload", "download"]
    ) -> None:
        """
        Transfer (i.e. upload or download) the entire project (i.e.
        every 'top level folder' (e.g. 'rawdata', 'derivatives').

        This function leverages the upload_all or download_all
        methods while switching the top level folder as defined in
        self.cfg that these methods use to determine the top-level
        folder to transfer.

        Parameters
        ----------

        direction : direction to transfer the data, either "upload" (from
                    local to central) or "download" (from central to local).
        """
        transfer_all_func = (
            self.upload_all if direction == "upload" else self.download_all
        )

        tmp_current_top_level_folder = copy.copy(self.cfg.top_level_folder)

        for folder_name in canonical_folders.get_top_level_folders():
            self.cfg.top_level_folder = folder_name
            transfer_all_func()

        self.cfg.top_level_folder = tmp_current_top_level_folder

    # -------------------------------------------------------------------------
    # SSH
    # -------------------------------------------------------------------------

    def _setup_ssh_key_and_rclone_config(self, log: bool = True) -> None:
        """
        Setup ssh connection, key pair (see ssh.setup_ssh_key)
        for details. Also, setup rclone config for ssh connection.
        """
        ssh.setup_ssh_key(self.cfg, log=log)

        self._setup_rclone_central_ssh_config(log)

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

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

        return f"central_{self.cfg.project_name}_{connection_method}"

    def _start_log(
        self,
        command_name: str,
        local_vars: Optional[dict] = None,
        store_in_temp_folder: bool = False,
        verbose: bool = True,
    ) -> None:
        """
        Initialize the logger. This is typically called at
        the start of public methods to initialize logging
        for a specific function call.

        Parameters
        ----------

        command_name : name of the command, for the log output files.

        local_vars : local_vars are passed to fancylog variables argument.
                 see ds_logger.wrap_variables_for_fancylog for more info

        store_in_temp_folder :
            if `False`, existing logging path will be used
            (local project .datashuttle).
        """
        if local_vars is None:
            variables = None
        else:
            variables = ds_logger.wrap_variables_for_fancylog(
                local_vars, self.cfg
            )

        if store_in_temp_folder:
            path_to_save = self._temp_log_path
            self._clear_temp_log_path()
        else:
            path_to_save = self.cfg.logging_path

        ds_logger.start(path_to_save, command_name, variables, verbose)

    def _move_logs_from_temp_folder(self) -> None:
        """
        Logs are stored within the project folder. Although
        in some instances, when setting configs, we do not know what
        the project folder is. In this case, make the logs
        in a temp folder in the .datashuttle config folder,
        and move them to the project folder once set.
        """
        if not self.cfg or not self.cfg["local_path"].is_dir():
            utils.log_and_raise_error(
                "Project folder does not exist. Logs were not moved.",
                FileNotFoundError,
            )

        ds_logger.close_log_filehandler()

        log_files = glob.glob(str(self._temp_log_path / "*.log"))
        for file_path in log_files:
            file_name = os.path.basename(file_path)

            shutil.move(
                self._temp_log_path / file_name,
                self.cfg.logging_path / file_name,
            )

    def _clear_temp_log_path(self) -> None:
        """"""
        log_files = glob.glob(str(self._temp_log_path / "*.log"))
        for file in log_files:
            os.remove(file)

    def _log_successful_config_change(self, message: bool = False) -> None:
        """
        Log the entire config at the time of config change.
        If messaged, just message "update successful" rather than
        print the entire configs as it becomes confusing.
        """
        if message:
            utils.print_message_to_user("Update successful.")
        utils.log(
            f"Update successful. New config file: "
            f"\n {self._get_json_dumps_config()}"
        )

    def _get_json_dumps_config(self) -> str:
        """
        Get the config dictionary formatted as json.dumps()
        which allows well formatted printing.
        """
        copy_dict = copy.deepcopy(self.cfg.data)
        self.cfg.convert_str_and_pathlib_paths(copy_dict, "path_to_str")
        return json.dumps(copy_dict, indent=4)

    def _make_project_metadata_if_does_not_exist(self) -> None:
        """
        Within the project local_path is also a .datashuttle
        folder that contains additional information, e.g. logs.
        """
        folders.make_folders(self.cfg.project_metadata_path, log=False)

    def _setup_rclone_central_ssh_config(self, log: bool) -> None:
        rclone.setup_central_as_rclone_target(
            "ssh",
            self.cfg,
            self.cfg.get_rclone_config_name("ssh"),
            self.cfg.ssh_key_path,
            log=log,
        )

    def _setup_rclone_central_local_filesystem_config(self) -> None:
        rclone.setup_central_as_rclone_target(
            "local_filesystem",
            self.cfg,
            self.cfg.get_rclone_config_name("local_filesystem"),
            self.cfg.ssh_key_path,
            log=True,
        )

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

    def _update_persistent_setting(
        self, setting_name: str, setting_value: Any
    ) -> None:
        """
        Load settings that are stored persistently across datashuttle
        sessions. These are stored in yaml dumped to dictionary.

        Parameters
        ----------
        setting_name : dictionary key of the persistent setting to change
        setting_value : value to change the persistent setting to
        """
        settings = self._load_persistent_settings()

        if setting_name not in settings:
            utils.raise_error(
                f"Setting key {setting_name} not found in "
                f"settings dictionary",
                KeyError,
            )

        settings[setting_name] = setting_value

        self._save_persistent_settings(settings)

    def _init_persistent_settings(self) -> None:
        """
        Initialise the default persistent settings
        and save to file.
        """
        settings = {"top_level_folder": "rawdata"}
        self._save_persistent_settings(settings)

    def _save_persistent_settings(self, settings: Dict) -> None:
        """
        Save the settings dict to file as .yaml
        """
        with open(self._persistent_settings_path, "w") as settings_file:
            yaml.dump(settings, settings_file, sort_keys=False)

    def _load_persistent_settings(self) -> Dict:
        """
        Load settings that are stored persistently across
        datashuttle sessions.
        """
        if not self._persistent_settings_path.is_file():
            self._init_persistent_settings()

        with open(self._persistent_settings_path, "r") as settings_file:
            settings = yaml.full_load(settings_file)
        return settings
