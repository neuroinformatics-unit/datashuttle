import copy
import getpass
import json
import os
import traceback
import warnings
from collections.abc import ItemsView
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import paramiko

from datashuttle.configs import Configs
from datashuttle.utils_mod import canonical_configs, rclone_utils, utils
from datashuttle.utils_mod.decorators import (  # noqa
    check_configs_set,
    requires_ssh_configs,
)
from datashuttle.utils_mod.directory_class import Directory

# --------------------------------------------------------------------------------------------------------------------
# Project Manager Class
# --------------------------------------------------------------------------------------------------------------------


class DataShuttle:
    """
    DataShuttle is a tool for convenient scientific
    project management and transfer in BIDS format.

    The expected organisation is a central repository
    on a remote machine  ('remote') that contains all
    project data. This is connected to multiple local
    machines ('local') which each contain a subset of
    the full project (e.g. machine for electrophysiology
    collection, machine for behavioural connection, machine
    for analysis for specific data etc.).

    On first use on a new profile, show warning prompting
    to set configurations with the function make_config_file().

    For transferring data between a remote data storage
    with SSH, use setup setup_ssh_connection_to_remote_server().
    This will allow you to check the server Key, add host key to
    profile if accepted, and setup ssh key pair.

    INPUTS: project_name - The project name to use the software under.
                           Each project has a root directory that is
                           specified during initial setup. Profile files
                           are stored in the Appdir directory
                           (platform specific). Use get_appdir_path()
                           to retrieve the path.
    """

    def __init__(self, project_name: str):

        if " " in project_name:
            utils.raise_error("project_name must not include spaces.")

        self.project_name = project_name
        self._appdir_path = utils.get_appdir_path(self.project_name)
        self._config_path = self._make_path("appdir", "config.yaml")

        self.cfg: Any = None
        self._ssh_key_path: Any = None
        self._data_type_dirs: Any = None
        self._top_level_dir_name = "rawdata"

        self._attempt_load_configs(prompt_on_fail=True)

        if self.cfg:
            self._set_attributes_after_config_load()

        rclone_utils.prompt_rclone_download_if_does_not_exist()

    def _set_attributes_after_config_load(self) -> None:
        """
        Once config file is loaded, update all private attributes
        according to config contents.

        The _data_type_dirs contains the entire directory tree for each
        data type. The structure is that the top-level directory
        (e.g. ephys, behav, microscopy) are found in
        the project root. Then sub- and ses- directory are created
        in this project root, and all subdirs are created at the
        session level.
        """
        self._ssh_key_path = self._make_path(
            "appdir", self.project_name + "_ssh_key"
        )
        self._hostkeys = self._make_path("appdir", "hostkeys")

        self._data_type_dirs = {
            "ephys": Directory(
                name="ephys",
                used=self.cfg["use_ephys"],
                level="ses",
            ),
            "behav": Directory(
                name="behav",
                used=self.cfg["use_behav"],
                level="ses",
            ),
            "funcimg": Directory(
                name="funcimg",
                used=self.cfg["use_funcimg"],
                level="ses",
            ),
            "histology": Directory(
                name="histology",
                used=self.cfg["use_histology"],
                level="sub",
            ),
        }

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
        Make a subject directory in the data type directory. By default,
        it will create the entire directory tree for this subject.

        :param sub_names:       subject name / list of subject names to make
                                within the directory (if not already, these
                                will be prefixed with sub/ses identifier)
        :param ses_names:       session names (same format as subject name).
                                If no session is provided, defaults to
                                "ses-001".
        :param data_type: The data_type to make the directory
                                in (e.g. "ephys", "behav", "histology"). If
                                "all" is selected, directory will be created
                                for all data type.
        """
        sub_names = self._format_names(sub_names, "sub")

        if ses_names is None:
            ses_names = [self.cfg.ses_prefix + "001"]

        else:
            ses_names = self._format_names(ses_names, "ses")

        self._make_directory_trees(
            sub_names,
            ses_names,
            data_type,
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
    ) -> None:
        """
        Upload data from a local machine to the remote project
        directory. In the case that a file / directory exists on
        the remote and local, the local will not be overwritten
        even if the remote file is an older version.

        :param sub_names: a list of sub names as accepted in make_sub_dir().
                          "all" will search for all subdirectories in the
                          data type directory to upload.
        :param ses_names: a list of ses names as accepted in make_sub_dir().
                          "all" will search each subdirectory for
                          ses- directories and upload all.
        :param dry_run: perform a dry-run of upload, to see which files
                        are moved.
        :param data_type: see make_sub_dir()
        """
        self._transfer_sub_ses_data(
            "upload", sub_names, ses_names, data_type, dry_run
        )

    def download_data(
        self,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        data_type: str = "all",
        dry_run: bool = False,
    ) -> None:
        """
        Download data from the remote project dir to the
        local computer. In the case that a file / dir
        exists on the remote and local, the local will
        not be overwritten even if the remote file is an
        older version.

        see upload_data() for inputs. "all" arguments will
        search the remote project for sub / ses to download.
        """
        self._transfer_sub_ses_data(
            "download", sub_names, ses_names, data_type, dry_run
        )

    def upload_project_dir_or_file(
        self, filepath: str, dry_run: bool = False
    ) -> None:
        """
        Upload an entire directory (including all subdirectories
        and files) from the local to the remote machine.

        :param filepath: a string containing the filepath to
                         move, relative to the project directory "rawdata"
                         or "derivatives" path (depending on which is currently
                         set), or full local path accepted.
        :param dry_run: dry_run the transfer (see which files
                        will be transferred without actually transferring)

        """
        processed_filepath = utils.get_path_after_base_dir(
            self._get_base_dir("local") / self._top_level_dir_name,
            Path(filepath),
        )

        self._move_dir_or_file(
            processed_filepath.as_posix(), "upload", dry_run
        )

    def download_project_dir_or_file(
        self, filepath: str, dry_run: bool = False
    ) -> None:
        """
        Download an entire directory (including all subdirectories
        and files) from the remote to the local machine.

        :param filepath: a string containing the filepath to
                         move, relative to the project directory "rawdata"
                         or "derivatives" path (depending on which is currently
                         set), or full remote path accepted.
        :param dry_run: dry_run the transfer (see which files
                         will be transferred without actually transferring)
        """
        processed_filepath = utils.get_path_after_base_dir(
            self._get_base_dir("remote") / self._top_level_dir_name,
            Path(filepath),
        )
        self._move_dir_or_file(
            processed_filepath.as_posix(), "download", dry_run
        )

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    @requires_ssh_configs
    def setup_ssh_connection_to_remote_server(self) -> None:
        """
        Setup a connection to the remote server using SSH.
        Assumes the remote_host_id and remote_host_username
        are set in the configuration file.

        First, the server key will be displayed, requiring
        verification of the server ID. This will store the
        hostkey for all future use.

        Next, prompt to input their password for the remote
        cluster. Once input, SSH private / public key pair
        will be setup (see _setup_ssh_key() for details).
        """
        verified = utils.verify_ssh_remote_host(
            self.cfg["remote_host_id"], self._hostkeys
        )

        if verified:
            self._setup_ssh_key()

    def write_public_key(self, filepath: str) -> None:
        """
        By default, the SSH private key only is stored on the local
        computer (in the Appdir directory). Use this function to generate
        the public key.

        :param filepath: full filepath (inc filename) to write the
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
        Initialise a config file for using the datashuttle on the
        local system. Once initialised, these settings will be
        used each time the datashuttle is opened.

        :param local_path:          path to project dir on local machine
        :param remote_path:         Filepath to remote project. If this is local
                                    (i.e. connection_method = "local_filesystem", this is
                                    the full path on the local filesystem
                                    (e.g. mounted drive)
                                    Otherwise, if this is via ssh
                                    (i.e. connection method = "ssh",
                                    this is the path to the project
                                    directory on remote machine.
                                    This should be a full path to remote
                                    directory i.e. this cannot include
                                    ~ home directory syntax, must contain
                                    the full path
                                    (e.g. /nfs/nhome/live/jziminski)
        :param connection_method    "local_filesystem" or "ssh"
        :param remote_host_id:      address for remote host for ssh connection
        :param remote_host_username:  username for which to login to
                                    remote host.
        :param use_ephys:           setting true will setup ephys directory
                                    tree on this machine
        :param use_funcimg:         create funcimg directory tree
        :param use_histology:       create histology directory tree
                                    directory on this machine
        :param use_behav:           create behav directory

        NOTE: higher level directory settings will override lower level
              settings (e.g. if ephys_behav_camera=True
              and ephys_behav=False, ephys_behav_camera will not be made).
        """
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
        self._setup_remote_as_rclone_target(
            "local_filesystem"
        )  # TODO: handle this!!

        utils.message_user(
            "Configuration file has been saved and "
            "options loaded into datashuttle."
        )

    def update_config(
        self, option_key: str, new_info: Union[str, bool]
    ) -> None:
        """
        Convenience function to update individual entry of configuration file.
        The config file, and currently loaded self.cfg will be updated.

        :param option_key: dictionary key of the option to change,
                           see make_config_file()
        :param new_info: value to update the config too
        """
        if not self.cfg:
            utils.raise_error(
                "Must have a config loaded before updating configs."
            )
        self.cfg.update_an_entry(option_key, new_info)
        self._set_attributes_after_config_load()

    def _attempt_load_configs(self, prompt_on_fail: bool) -> None:
        """
        Attempt to load the config file. If it does not exist or crashes
        when attempt to load from file, return False.

        :param prompt_on_fail: if config file not found, or crashes on load,
                               show warning.

        :return: loaded dictionary, or False if not loaded.
        """
        exists = self._config_path.is_file()

        if not exists and prompt_on_fail:
            warnings.warn(
                "Configuration file has not been initialized. "
                "Use make_config_file() to setup before continuing."
            )
            return

        self.cfg = Configs(self._config_path, None)

        try:
            self.cfg.load_from_file()
        except Exception:
            self.cfg = None

            if prompt_on_fail:
                utils.message_user(
                    f"Config file failed to load. Check file "
                    f"formatting at {self._config_path.as_posix()}. If "
                    f"cannot load, re-initialise configs with "
                    f"make_config_file()"
                )

    # --------------------------------------------------------------------------------------------------------------------
    # Public Getters
    # --------------------------------------------------------------------------------------------------------------------

    def get_local_path(self) -> None:
        """
        Return the project local path.
        """
        utils.message_user(self.cfg["local_path"].as_posix())

    def get_appdir_path(self) -> None:
        """
        Return the system appdirs path where
        project settings are stored.
        """
        utils.message_user(self._appdir_path.as_posix())

    def get_config_path(self) -> None:
        """
        Return the full path to the DataShuttle config file.
        """
        utils.message_user(self._config_path.as_posix())

    def get_remote_path(self) -> None:
        """
        Return the project remote path.
        This is always formatted to UNIX style.
        """
        utils.message_user(self.cfg["remote_path"].as_posix())

    def show_configs(self) -> None:
        """
        Print the current configs to the terminal.
        """
        copy_dict = copy.deepcopy(self.cfg.data)
        self.cfg.convert_str_and_pathlib_paths(copy_dict, "path_to_str")
        utils.message_user(json.dumps(copy_dict, indent=4))

    def supply_config_file(
        self, input_path_to_config: str, warn: bool = True
    ) -> None:

        path_to_config = Path(input_path_to_config)

        utils.raise_error_not_exists_or_not_yaml(path_to_config)

        if warn:
            input_ = utils.get_user_input(
                "This will overwrite the existing datashuttle config file."
                "If you wish to proceed, press y."
            )

            if input_ != "y":
                return None

        try:
            new_cfg: Configs

            new_cfg = Configs(path_to_config, None)
            new_cfg.load_from_file()

            new_cfg = canonical_configs.handle_cli_or_supplied_config_bools(
                new_cfg
            )
            new_cfg.check_dict_values_and_inform_user()

        except BaseException:
            utils.message_user(traceback.format_exc())
            utils.raise_error(
                "Could not load config file. Please check that "
                "the file is formatted correctly. "
                "Config file was not updated."
            )
            return None

        self.cfg = new_cfg
        self._set_attributes_after_config_load()
        self.cfg.file_path = self._config_path
        self.cfg.dump_to_file()
        utils.message_user("Update successful.")

    @staticmethod
    def check_name_processing(names: Union[str, list], prefix: str) -> None:
        """
        Pass list of names to check how these will be auto-formatted.
        Useful for checking tags e.g. @TO@, @DATE@, @DATETIME@, @DATE@

        :param A string or list of names to check how they will be processed
        :param prefix, "sub-" or "ses-"
        """
        if prefix not in ["sub-", "ses-"]:
            utils.raise_error("prefix: must be 'sub-' or 'ses-'")

        processed_names = utils.format_names(names, prefix)
        utils.message_user(processed_names)

    # --------------------------------------------------------------------------------------------------------------------
    # Setup RClone
    # --------------------------------------------------------------------------------------------------------------------

    def _move_dir_or_file(
        self, filepath: str, upload_or_download: str, dry_run: bool
    ) -> None:
        """
        Copy a directory or file with Rclone.

        :param filepath: filepath (not including local
                         or remote root) to copy
        :param upload_or_download: upload goes local to
                                   remote, download goes
                                   remote to local
        :param dry_run: do not actually move the files,
                        just report what would be moved.
        """
        local_filepath = self._make_path(
            "local", [self._top_level_dir_name, filepath]
        ).as_posix()

        remote_filepath = self._make_path(
            "remote", [self._top_level_dir_name, filepath]
        ).as_posix()

        extra_arguments = "--create-empty-src-dirs"
        if dry_run:
            extra_arguments += " --dry-run"

        if upload_or_download == "upload":

            rclone_utils.call_rclone(
                f"copy "
                f'"{local_filepath}" '
                f'"{self._get_rclone_config_name(self.cfg["connection_method"])}:'
                f'{remote_filepath}" '
                f"{extra_arguments}"
            )

        elif upload_or_download == "download":
            rclone_utils.call_rclone(
                f"copy "
                f'"{self._get_rclone_config_name(self.cfg["connection_method"])}:'
                f'{remote_filepath}" '
                f'"{local_filepath}"  '
                f"{extra_arguments}"
            )

    def _setup_remote_as_rclone_target(self, connection_method: str) -> None:
        """
        rclone shares config file so need to create
        new local and remote for all project
        :param local_or_ssh:
        """
        rclone_config_name = self._get_rclone_config_name(
            connection_method,
        )

        rclone_utils.setup_remote_as_rclone_target(
            self.cfg, connection_method, rclone_config_name, self._ssh_key_path
        )

    def _get_rclone_config_name(self, connection_method: str) -> str:
        return f"remote_{self.project_name}_{connection_method}"

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
    ) -> None:
        """
        Entry method to make a full directory tree. It will
        iterate through all passed subjects, then sessions, then
        subdirs within a data_type directory. This
        permits flexible creation of directories (e.g.
        to make subject only, do not pass session name.

        Ensure sub and ses names are already formatted
        before use in this function.

        :param sub_names:       subject name / list of subject names
                                to make within the directory
                                (if not already, these will be prefixed
                                with sub/ses identifier)
        :param ses_names:       session names (same format as subject
                                name). If no session is provided, defaults
                                to "ses-001".

                                Note if ses name contains @DATE@ or @DATETIME@,
                                this text will be replaced with the date /
                                datetime at the time of directory creation.

        """
        if not self._check_data_type_is_valid(data_type, prompt_on_fail=True):
            return

        for sub in sub_names:

            sub_path = self._make_path(
                "local", [self._top_level_dir_name, sub]
            )

            utils.make_dirs(sub_path)

            self._make_data_type_folders(data_type, sub_path, "sub")

            for ses in ses_names:

                ses_path = self._make_path(
                    "local", [self._top_level_dir_name, sub, ses]
                )

                utils.make_dirs(ses_path)

                self._make_data_type_folders(data_type, ses_path, "ses")

    def _make_data_type_folders(
        self,
        data_type: Union[list, str],
        sub_or_ses_level_path: Path,
        level: str,
    ) -> None:
        """ """
        data_type_items = self._get_data_type_items(data_type)

        for data_type_key, data_type_dir in data_type_items:  # type: ignore

            if data_type_dir.used and data_type_dir.level == level:

                data_type_path = sub_or_ses_level_path / data_type_dir.name

                utils.make_dirs(data_type_path)

                utils.make_datashuttle_metadata_folder(data_type_path)

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
    ) -> None:
        """
        Iterate through all data type, sub, ses and transfer session directory.

        :param upload_or_download: "upload" or "download"
        :param sub_names: see make_sub_dir()
        :param ses_names: see make_sub_dir()
        :param data_type: see make_sub_dir()
        :param dry_run: see upload_project_dir_or_file*(
        """
        local_or_remote = (
            "local" if upload_or_download == "upload" else "remote"
        )

        # Find sub names to transfer
        if sub_names not in ["all", ["all"]]:
            sub_names = self._format_names(sub_names, "sub")
        else:
            sub_names = self._search_subs_from_project_dir(
                local_or_remote,
                self._top_level_dir_name,
            )

        for sub in sub_names:

            self._transfer_data_type(
                upload_or_download,
                local_or_remote,
                data_type,
                sub,
                dry_run=dry_run,
            )

            # Find ses names  to transfer
            if ses_names not in ["all", ["all"]]:
                ses_names = self._format_names(ses_names, "ses")
            else:
                ses_names = self._search_ses_from_sub_dir(
                    local_or_remote, self._top_level_dir_name, sub
                )

            for ses in ses_names:

                self._transfer_data_type(
                    upload_or_download,
                    local_or_remote,
                    data_type,
                    sub,
                    ses,
                    dry_run,
                )

    def _transfer_data_type(
        self,
        upload_or_download: str,
        local_or_remote: str,
        data_type: Union[list, str],
        sub: str,
        ses: Optional[str] = None,
        dry_run: bool = False,
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
                    filepath, upload_or_download, dry_run=dry_run
                )

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
        """
        if data_type not in ["all", ["all"]]:
            data_type_items = self._get_data_type_items(
                data_type,
            )
        else:
            data_type_items = self._search_data_dirs_sub_or_ses_level(
                local_or_remote,
                sub,
                ses,
            )
        return data_type_items

    # --------------------------------------------------------------------------------------------------------------------
    # Search for subject and sessions (local or remote)
    # --------------------------------------------------------------------------------------------------------------------

    def _search_subs_from_project_dir(
        self, local_or_remote: str, data_type: str
    ) -> List[str]:
        """
        Search a datatype directory for all present sub-prefixed directories.
        If remote, ssh or filesystem will be used depending on config.

        :param local_or_remote: "local" or "remote"
        :param data_type: the data type (e.g. behav, cannot be "all")
        """
        search_path = self._make_path(
            local_or_remote, [self._top_level_dir_name]
        )

        search_prefix = self.cfg.sub_prefix + "*"
        return self._search_for_directories(
            local_or_remote, search_path, search_prefix
        )

    def _search_ses_from_sub_dir(
        self, local_or_remote: str, data_type: str, sub: str
    ) -> List[str]:
        """
        See _search_subs_from_project_dir(), same but for searching sessions
        within a subdirectory.
        """
        search_path = self._make_path(
            local_or_remote, [self._top_level_dir_name, sub]
        )
        search_prefix = self.cfg.ses_prefix + "*"

        return self._search_for_directories(
            local_or_remote, search_path, search_prefix
        )

    def _search_data_dirs_sub_or_ses_level(
        self, local_or_remote: str, sub: str, ses: Optional[str] = None
    ) -> zip:
        """
        Find data_type type directories in the project base
        directory (e.g. "ephys", "behav"), (by filtering the
        names of all directories present).  Return these in the
        same format as dict.items()

        :param local_or_remote: "local" or "remote
        """
        base_dir = (
            self._get_base_dir(local_or_remote)
            / self._top_level_dir_name
            / sub
        )
        if ses:
            base_dir = base_dir / ses

        directory_names = self._search_for_directories(
            local_or_remote, base_dir, "*"
        )

        data_directories = self._process_glob_to_find_data_type_dirs(
            directory_names
        )

        return data_directories

    def _search_for_directories(
        self, local_or_remote: str, search_path: Path, search_prefix: str
    ) -> List[str]:
        """
        Wrapper to determine the method used to search for search
        prefix directories in the search path.

        :param local_or_remote: "local" or "remote"
        :param search_path: full filepath to search in
        :param search_prefix: file / dirname to search (e.g. "sub-*")
        """
        if (
            local_or_remote == "remote"
            and self.cfg["connection_method"] == "ssh"
        ):

            all_dirnames = utils.search_ssh_remote_for_directories(
                search_path,
                search_prefix,
                self.cfg,
                self._hostkeys,
                self._ssh_key_path,
            )
        else:
            all_dirnames = utils.search_filesystem_path_for_directories(
                search_path / search_prefix
            )
        return all_dirnames

    def _process_glob_to_find_data_type_dirs(
        self,
        directory_names: list,
    ) -> zip:
        """
        Process the results of glob on a sub or session level,
        which could contain any kind of folder / file.
        Find the data_type files and return in
        a format that mirros dict.items()
        """
        ses_dir_keys = []
        ses_dir_values = []
        for dir_name in directory_names:
            data_type_key = [
                key
                for key, value in self._data_type_dirs.items()
                if value.name == dir_name
            ]

            if data_type_key:
                ses_dir_keys.append(data_type_key[0])
                ses_dir_values.append(self._data_type_dirs[data_type_key[0]])

        return zip(ses_dir_keys, ses_dir_values)

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    @requires_ssh_configs
    def _setup_ssh_key(self) -> None:
        """
        Setup an SSH private / public key pair with
        remote server. First, a private key is generated
        in the appdir. Next a connection requiring input
        password made, and the public part of the key
        added to ~/.ssh/authorized_keys.
        """
        utils.generate_and_write_ssh_key(self._ssh_key_path)

        password = getpass.getpass(
            "Please enter password to your remote host to add the public key. "
            "You will not have to enter your password again."
        )

        key = paramiko.RSAKey.from_private_key_file(
            self._ssh_key_path.as_posix()
        )

        utils.add_public_key_to_remote_authorized_keys(
            self.cfg, self._hostkeys, password, key
        )

        self._setup_remote_as_rclone_target("ssh")
        utils.message_user(
            f"SSH key pair setup successfully. "
            f"Private key at: {self._ssh_key_path.as_posix()}"
        )

    # --------------------------------------------------------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------------------------------------------------------

    def _make_path(self, base: str, subdirs: Union[str, list]) -> Path:
        """
        Function for joining relative path to base dir.
        If path already starts with base dir, the base
        dir will not be joined.

        :param base: "local", "remote" or "appdir"
        :param subdirs: a list (or string for 1) of
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
        """
        if base == "local":
            base_dir = self.cfg["local_path"]
        elif base == "remote":
            base_dir = self.cfg["remote_path"]
        elif base == "appdir":
            base_dir = utils.get_appdir_path(self.project_name)
        return base_dir

    def _format_names(
        self, names: Union[list, str], sub_or_ses: str
    ) -> Union[str, list]:
        """
        :param names: str or list containing sub or ses names
                      (e.g. to make dirs)
        :param sub_or_ses: "sub" or "ses" - this defines the prefix checks.
        """
        prefix = self._get_sub_or_ses_prefix(sub_or_ses)
        processed_names = utils.format_names(names, prefix)

        return processed_names

    def _get_sub_or_ses_prefix(self, sub_or_ses: str) -> str:
        """
        Get the sub / ses prefix (default is sub- and ses-") set in cfgs.
        """
        if sub_or_ses == "sub":
            prefix = self.cfg.sub_prefix
        elif sub_or_ses == "ses":
            prefix = self.cfg.ses_prefix
        return prefix

    def _check_data_type_is_valid(
        self, data_type: str, prompt_on_fail: bool
    ) -> bool:
        """
        Check the passed experiemnt_type is valid (must
        be a key on self.ses_dirs or "all")
        """
        if type(data_type) == list:
            valid_keys = list(self._data_type_dirs.keys()) + ["all"]
            is_valid = all([type in valid_keys for type in data_type])
        else:
            is_valid = (
                data_type in self._data_type_dirs.keys() or data_type == "all"
            )

        if prompt_on_fail and not is_valid:
            utils.message_user(
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
        them (stored in self._data_type_dirs or a single item.
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
