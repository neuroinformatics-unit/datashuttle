import copy
import fnmatch
import getpass
import glob
import os
import stat
import warnings
from functools import wraps
from pathlib import Path
from typing import Union, cast

import appdirs
import paramiko
import yaml
from ftpsync.sftp_target import SFTPTarget
from ftpsync.synchronizers import DownloadSynchronizer, UploadSynchronizer
from ftpsync.targets import FsTarget

# --------------------------------------------------------------------------------------------------------------------
# Directory Class
# --------------------------------------------------------------------------------------------------------------------


class Directory:
    """
    Directory class used to contain details of canonical
    directories in the project directory tree.
    """

    def __init__(self, name, used, subdirs=None):
        self.name = name
        self.used = used
        self.subdirs = subdirs


# --------------------------------------------------------------------------------------------------------------------
# Class Decorators
# --------------------------------------------------------------------------------------------------------------------


def requires_ssh_configs(func):
    """
    Decorator to check file is loaded. Used on Mainwindow class
    methods only as first arg is assumed to be self (containing cfgs)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if (
            not args[0].cfg["remote_host_id"]
            or not args[0].cfg["remote_host_username"]
        ):
            args[0]._raise_error(
                "Cannot setup SSH connection, configuration file remote_host_id or"
                " remote_host_username is not set."
            )
        else:
            return func(*args, **kwargs)

    return wrapper


# --------------------------------------------------------------------------------------------------------------------
# Project Manager Class
# --------------------------------------------------------------------------------------------------------------------


class ProjectManager:
    """
    Main project manager class for data organisation and transfer in BIDS-style project directory.
    The expected organisation is a central repository on a remote machine ('remote') that
    contains all project data. This is connected to multiple local machines ('local') which
    each contain a subset of the full project (e.g. machine for electrophysiology collection,
    machine for behavioural connection, machine for analysis for specific data etc.).

    On first use on a new profile, the user will be prompted to set configurations with the function
    make_config_file().

    For transferring data between a remote data storage with SSH, use setup setup_ssh_connection_to_remote_server().
    This will allow you to check the server Key, add host key to profile if accepted, and setup ssh key pair.

    INPUTS: project_name - The project name to use the software under. Each project has a root directory
                           that is specified during initial setup. Profile files are stored in the Appdir directory
                           (platform specific). Use get_appdir_path() to retrieve the path.
    """

    def __init__(self, project_name: str):
        self.project_name = project_name

        self._config_path = self._join("appdir", "config.yaml")
        self.cfg = self._attempt_load_configs(prompt_on_fail=True)

        if self.cfg:
            self._ssh_key_path = None
            self._ses_dirs = None

            if self.cfg:
                self.set_attributes_after_config_load()

    def set_attributes_after_config_load(self):
        """
        Once config file is loaded, update all private attributes according to config contents.

        The _ses_dirs contains the entire directory tree for each data type.
        The structure is that the top-level directory (e.g. ephys, behav, microscopy) are found in
        the project root. Then sub- and ses- directory are created in this project root, and
        all subdirs are created at the session level.
        """
        self._ssh_key_path = self._join(
            "appdir", self.project_name + "_ssh_key"
        )
        self._hostkeys = self._join("appdir", "hostkeys")

        self._ses_dirs = {
            "ephys": Directory(
                "ephys",
                self.cfg["use_ephys"],
                subdirs={
                    "ephys_behav": Directory(
                        "behav",
                        self.cfg["use_ephys_behav"],
                        subdirs={
                            "ephys_behav_camera": Directory(
                                "camera",
                                self.cfg["use_ephys_behav_camera"],
                            ),
                        },
                    ),
                },
            ),
            "behav": Directory(
                "behav",
                self.cfg["use_behav"],
                subdirs={
                    "behav_camera": Directory(
                        "camera", self.cfg["use_behav_camera"]
                    ),
                },
            ),
            "imaging": Directory(
                "imaging",
                self.cfg["use_imaging"],
            ),
            "histology": Directory(
                "histology",
                self.cfg["use_histology"],
            ),
        }

    # --------------------------------------------------------------------------------------------------------------------
    # Public Directory Makers
    # --------------------------------------------------------------------------------------------------------------------

    def make_sub_dir(
        self,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list] = None,
        make_ses_tree: bool = True,
    ):
        """
        Make a subject directory in the data type directory. By default, it will create
        the entire directory tree for this subject.

        :param experiment_type: The experiment_type to make the directory in (e.g. "ephys", "behav",
                                "microscopy"). If "all" is selected, directory will be created for all data type.
        :param sub_names:       subject name / list of subject names to make within the directory (if not
                                already, these will be prefixed with sub/ses identifier)
        :param ses_names:       session names (same format as subject name). If no session is provided, defaults to "ses-001".
        :param make_ses_tree:   option to make the entire session tree under the subject directory. If False, the subject
                                directory only will be created.
        """
        sub_names = self._process_names(sub_names, "sub")

        if make_ses_tree:
            if ses_names is None:
                ses_names = [self.cfg["ses_prefix"] + "001"]
            else:
                ses_names = self._process_names(ses_names, "ses")
        else:
            ses_names = []

        self._make_directory_trees(
            experiment_type,
            sub_names,
            ses_names,
            make_ses_tree,
            process_names=False,
        )

    def make_ses_dir(
        self,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        make_ses_tree: bool = True,
    ):
        """
        See make_sub_dir() for inputs.
        """
        self._make_directory_trees(
            experiment_type, sub_names, ses_names, make_ses_tree
        )

    def make_ses_tree(
        self,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
    ):
        """
        See make_sub_dir() for inputs.
        """
        self._make_directory_trees(experiment_type, sub_names, ses_names)

    # --------------------------------------------------------------------------------------------------------------------
    # Public File Transfer
    # --------------------------------------------------------------------------------------------------------------------

    def upload_data(
        self,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        preview: bool = False,
    ):
        """
        Upload data from a local machine to the remote project directory.
        In the case that a file / directory exists on the remote and local, the local will
        not be overwritten even if the remote file is an older version.

        :param experiment_type: see make_sub_dir()
        :param sub_names: a list of sub names as accepted in make_sub_dir(). "all" will search for all
                          sub- directories in the data type directory to upload.
        :param ses_names: a list of ses names as accepted in make_sub_dir(). "all" will search each
                          sub- directory for ses- directories and upload all.
        :param preview: perform a dry-run of upload, to see which files are moved.
        """
        self._transfer_sub_ses_data(
            "upload", experiment_type, sub_names, ses_names, preview
        )

    def download_data(
        self,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        preview: bool = False,
    ):
        """
        Download data from the remote project dir to the local computer.
        In the case that a file / dir exists on the remote and local, the local will
        not be overwritten even if the remote file is an older version.

        see upload_data() for inputs. "all" arguments will search the remote project
        for sub / ses to download.
        """
        self._transfer_sub_ses_data(
            "download", experiment_type, sub_names, ses_names, preview
        )

    def upload_project_dir_or_file(self, filepath: str, preview: bool = False):
        """
        Upload an entire directory (including all subdirectories and files) from the local
        to the remote machine

        :param filepath: a string containing the filepath to move, relative to the project directory
        :param preview: preview the transfer (see which files will be transferred without actually transferring)

        """
        self._move_dir_or_file(filepath, "upload", preview)

    def download_project_dir_or_file(
        self, filepath: str, preview: bool = False
    ):
        """
        Download an entire directory (including all subdirectories and files) from the local
        to the remote machine.

        see upload_project_dir_or_file() for inputs
        """
        self._move_dir_or_file(filepath, "download", preview)

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    @requires_ssh_configs
    def setup_ssh_connection_to_remote_server(self):
        """
        Setup a connection to the remote server using SSH. Assumes the remote_host_id and
        remote_host_username are set in the configuration file.

        First, the server key will be displayed and the user will confirm connection
        to the server. This will store the hostkey for all future use.

        Next, the user is prompted to input their password for the remote cluster.
        Once input, SSH private / public key pair will be setup (see _setup_ssh_key()
        for details).
        """
        verified = self._verify_ssh_remote_host()

        if verified:
            self._setup_ssh_key()

    def write_public_key(self, filepath: str):
        """
        By default, the SSH private key only is stored on the local
        computer (in the Appdir directory). Use this function to generate
        the public key.

        :param filepath: full filepath (inc filename) to write the public key to.
        """
        key = paramiko.RSAKey.from_private_key_file(self._ssh_key_path)

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
        ssh_to_remote: bool,
        remote_host_id: str = None,
        remote_host_username: str = None,
        sub_prefix: str = "sub-",
        ses_prefix: str = "ses-",
        use_ephys: bool = True,
        use_ephys_behav: bool = True,
        use_ephys_behav_camera: bool = True,
        use_behav: bool = True,
        use_behav_camera: bool = True,
        use_imaging: bool = True,
        use_histology: bool = True,
    ):
        """
        Initialise a config file for using the project manager on the local system. Once initialised, these
        settings will be used each time the project manager is opened.

        :param local_path:                  path to project dir on local machine
        :param remote_path:                 path to project directory on remote machine. Note this cannot
                                            include ~ home directory syntax, must contain the full path (
                                            e.g. /nfs/nhome/live/jziminski)
        :param ssh_to_remote                if true, ssh will be used to connect to remote cluster and
                                            remote_host_id, remote_host_username must be provided.
        :param remote_host_id:              address for remote host for ssh connection
        :param remote_host_username:        username for which to login to remote host.
        :param sub_prefix:                  prefix for all subject (i.e. mouse) level directory. Default is BIDS: "sub-"
        :param ses_prefix:                  prefix for all session level directory. Default is BIDS: "ses-"
        :param use_ephys:                   setting true will setup ephys directory tree on this machine
        :param use_imaging:                 create imaging directory tree
        :param use_histology:               create histology directory tree
        :param use_ephys_behav:             create behav directory in ephys directory on this machine
        :param use_ephys_behav_camera:      create camera directory in ephys behaviour directory on this machine
        :param use_behav:                   create behav directory
        :param use_behav_camera:            create camera directory in behav directory

        NOTE: higher level directory settings will override lower level settings (e.g. if ephys_behav_camera=True
              and ephys_behav=False, ephys_behav_camera will not be made).
        """
        if remote_path[0] == "~":
            self._raise_error(
                "remote_path must contain the full directory path with no ~ syntax"
            )

        if ssh_to_remote is True and (
            not remote_host_id or not remote_host_username
        ):
            self._raise_error(
                "ssh to remote set but no remote_host_id or remote_host_username not"
                " provided"
            )

        if ssh_to_remote is False and (remote_host_id or remote_host_username):
            warnings.warn(
                "SSH to remote is false, but remote_host_id or remote_host_username"
                " provided"
            )

        config_dict = {
            "local_path": local_path,
            "remote_path": remote_path,
            "ssh_to_remote": ssh_to_remote,
            "remote_host_id": remote_host_id,
            "remote_host_username": remote_host_username,
            "sub_prefix": sub_prefix,
            "ses_prefix": ses_prefix,
            "use_ephys": use_ephys,
            "use_imaging": use_imaging,
            "use_histology": use_histology,
            "use_ephys_behav": use_ephys_behav,
            "use_ephys_behav_camera": use_ephys_behav_camera,
            "use_behav": use_behav,
            "use_behav_camera": use_behav_camera,
        }

        self._dump_configs_to_file(config_dict)

        self.cfg = self._attempt_load_configs(prompt_on_fail=False)
        self.set_attributes_after_config_load()
        self._message_user(
            "Configuration file has been saved and options loaded into the project"
            " manager."
        )

    def update_config(self, option_key: str, new_info: Union[str, bool]):
        """
        Convenience function to update individual entry of configuration file.
        The config file, and currently loaded self.cfg will be updated.

        :param option_key: dictionary key of the option to change,
                           see make_config_file()
        :param new_info: value to update the config too
        """
        if option_key in ["local_path", "remote_path"]:
            new_info = Path(new_info)

        self.cfg[option_key] = new_info
        self.set_attributes_after_config_load()
        self._save_cfg_to_configs_file()

    # --------------------------------------------------------------------------------------------------------------------
    # Public Getters
    # --------------------------------------------------------------------------------------------------------------------

    def get_local_path(self):
        return self.cfg["local_path"].as_posix()

    def get_appdir_path(self):
        return self._get_user_appdir_path().as_posix()

    def get_remote_path(self):
        return self.cfg["remote_path"].as_posix()

    # ====================================================================================================================
    # Private Functions
    # ====================================================================================================================

    # --------------------------------------------------------------------------------------------------------------------
    # Make Directory Trees
    # --------------------------------------------------------------------------------------------------------------------

    def _make_directory_trees(
        self,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        make_ses_tree: bool = True,
        process_names: bool = True,
    ):
        """
        Entry method to make a full directory tree. It will iterate through all
        passed subjects, then sessions, then subdirs within a experiment_type directory. This
        permits flexible creation of directories (e.g. to make subject only, do not pass session name.

        subject and session names are first processed to ensure correct format.

        :param experiment_type: The experiment_type to make the directory in (e.g. "ephys", "behav", "microscopy").
                                If "all" is selected, directory will be created for all data type.
        :param sub_names:       subject name / list of subject names to make within the directory
                                (if not already, these will be prefixed with sub/ses identifier)
        :param ses_names:       session names (same format as subject name). If no session is
                                provided, defaults to "ses-001".
        :param make_ses_tree:   option to make the entire session tree under the subject directory.
                                If False, the subject directory only will be created.
        :param process_names:   option to process names or not (e.g. if names were processed already).

        """
        sub_names = (
            self._process_names(sub_names, "sub")
            if process_names
            else sub_names
        )
        ses_names = (
            self._process_names(ses_names, "ses")
            if process_names
            else ses_names
        )

        if not self._check_experiment_type_is_valid(
            experiment_type, prompt_on_fail=True
        ):
            return

        experiment_type_items = self._get_experiment_type_items(
            experiment_type
        )

        for experiment_type_key, experiment_type_dir in experiment_type_items:
            if experiment_type_dir.used:
                self._make_dirs(self._join("local", experiment_type_dir.name))

                for sub in sub_names:
                    self._make_dirs(
                        self._join("local", [experiment_type_dir.name, sub])
                    )

                    for ses in ses_names:
                        self._make_dirs(
                            self._join(
                                "local", [experiment_type_dir.name, sub, ses]
                            )
                        )

                        if make_ses_tree:
                            self._make_ses_directory_tree(
                                sub, ses, experiment_type_key
                            )

    def _make_ses_directory_tree(
        self, sub: str, ses: str, experiment_type_key: str
    ):
        """
        Make the directory tree within a session. This is dependent on the experiment_type (e.g. "ephys")
        dir and defined in the subdirs field on the Directory class, in self._ses_dirs.

        All subdirs will be made recursively, unless the .used attribute on the Directory class is
        False. This will also stop and subdirs of the subdir been created.

        :param sub:                    subject name to make directory tree in
        :param ses:                    session name to make directory tree in
        :param experiment_type_key:    experiment_type_key (e.g. "ephys") to make directory tree in.
                                       Note this defines the subdirs created.
        """
        experiment_type_dir = self._ses_dirs[experiment_type_key]

        if experiment_type_dir.used and experiment_type_dir.subdirs:
            self._recursive_make_subdirs(
                directory=experiment_type_dir,
                path_to_dir=[experiment_type_dir.name, sub, ses],
            )

    def _recursive_make_subdirs(self, directory: Directory, path_to_dir: list):
        """
        Function to recursively create all directories in a Directory .subdirs field.

        i.e. this will first create a directory based on the .name attribute. It will then
        loop through all .subdirs, and do the same - recursively looping through subdirs
        until the entire directory tree is made. If .used attribute on a directory is False,
        that directory and all subdirs of the directory will not be made.

        :param directory:
        :param path_to_dir:
        """
        if directory.subdirs:
            for subdir in directory.subdirs.values():
                if subdir.used:
                    new_path_to_dir = path_to_dir + [subdir.name]
                    self._make_dirs(self._join("local", new_path_to_dir))
                    self._recursive_make_subdirs(subdir, new_path_to_dir)

    # --------------------------------------------------------------------------------------------------------------------
    # File Transfer
    # --------------------------------------------------------------------------------------------------------------------

    def _transfer_sub_ses_data(
        self,
        upload_or_download: str,
        experiment_type: str,
        sub_names: Union[str, list],
        ses_names: Union[str, list],
        preview: bool,
    ):
        """
        Iterate through all data type, sub, ses and transfer session directory.

        :param upload_or_download: "upload" or "download"
        :param experiment_type: see make_sub_dir()
        :param sub_names: see make_sub_dir()
        :param ses_names: see make_sub_dir()
        :param preview: see upload_project_dir_or_file*(
        """
        dir_to_search = "local" if upload_or_download == "upload" else "remote"

        experiment_type_items = self._get_experiment_type_items(
            experiment_type
        )

        for experiment_type_key, experiment_type_dir in experiment_type_items:
            if sub_names != "all":
                sub_names = self._process_names(sub_names, "sub")
            else:
                sub_names = self._search_subs_from_project_dir(
                    dir_to_search, experiment_type_key
                )

            for sub in sub_names:
                if ses_names != "all":
                    ses_names = self._process_names(ses_names, "ses")
                else:
                    ses_names = self._search_ses_from_sub_dir(
                        dir_to_search, experiment_type_key, sub
                    )

                for ses in ses_names:
                    filepath = os.path.join(experiment_type_dir.name, sub, ses)
                    self._move_dir_or_file(
                        filepath, upload_or_download, preview=preview
                    )

    def _move_dir_or_file(
        self, filepath: str, upload_or_download: str, preview: bool
    ):
        """
        High-level function for transferring directories or files with pyftpsync.
        Adds the filepath provided to the remote and local base dir, wraps
        in the appropriate pyftpsync Target class (e.g. filesystem vs. ssh)
        and uses the appropriate syncronizer (upload or download) to transfer
        the directory (and all subdirs, files).

        :param filepath: relative project filepath to move
        :param upload_or_download: "upload" or "download"
        :param preview:  see upload_project_dir_or_file*(
        """
        local_filepath = self._join("local", filepath)
        remote_filepath = self._join("remote", filepath)

        local = FsTarget(local_filepath)
        remote = self._get_remote_target(remote_filepath)

        opts = self._get_default_syncronizer_opts(preview)

        syncronizer = self._get_syncronizer(upload_or_download)
        s = syncronizer(local, remote, opts)
        s.run()

    def _get_syncronizer(self, upload_or_download: str):
        """
        Convenience function to get the pyftpsync syncronizer
        """
        if upload_or_download == "upload":
            syncronizer = UploadSynchronizer

        elif upload_or_download == "download":
            syncronizer = DownloadSynchronizer

        return syncronizer

    def _get_remote_target(self, remote_filepath: str):
        """
        Convenience function to get the pyftsync target
        based on remote connection type.
        """
        if self.cfg["ssh_to_remote"]:
            remote = SFTPTarget(
                remote_filepath,
                self.cfg["remote_host_id"],
                username=self.cfg["remote_host_username"],
                private_key=self._ssh_key_path,
                hostkeys=self._hostkeys,
            )

        else:
            remote = FsTarget(remote_filepath)

        return remote

    def _get_default_syncronizer_opts(self, preview: bool):
        """
        Retrieve the default options for upload and download. These
        are very important as define the behaviour of file transfer
        when there are conflicts (e.g. whether to delete remote
        file if it is not found on the local filesystem).

        Currently, all options are set so that no file is ever overwritten.
        If there is a remote directory that is older than the local directory, it will not
        be overwritten. The only 'overwrite' that occurs is if the remote
        or local directory has been deleted - by default this will not be replaced as
        pyftpsync metadata indicates the file has been deleted. Using the default
        'force' option will force file transfer, but also has other effects e.g.
        overwriting newer files with old, which we dont want. This option has been
        edited to permit a "restore" argumnent, which acts Force=False except
        in the case where the local / remote file has been deleted entirely, in which
        case it will be replaced.

        :param preview: run pyftpsync's "dry_run" option.
        """
        opts = {
            "help": False,
            "verbose": 5,
            "quiet": 0,
            "debug ": False,
            "case": "strict",
            "dry_run": preview,
            "progress": False,
            "no_color": True,
            "ftp_active": False,
            "migrate": False,
            "no_verify_host_keys": False,
            # "match": 3,
            # "exclude": 3,
            "prompt": False,
            "no_prompt": False,
            "no_keyring": True,
            "no_netrc": True,
            "store_password": False,
            "force": "restore",
            "resolve": "ask",
            "delete": False,
            "delete_unmatched": False,
            "create_dir": True,
            "report_problems": False,
        }

        return opts

    # --------------------------------------------------------------------------------------------------------------------
    # Search for subject and sessions (local or remote)
    # --------------------------------------------------------------------------------------------------------------------

    def _search_subs_from_project_dir(
        self, local_or_remote: str, experiment_type: str
    ):
        """
        Search a datatype directory for all present sub- prefixed directories.
        If remote, ssh or filesystem will be used depending on config.

        :param local_or_remote: "local" or "remote"
        :param experiment_type: the data type (e.g. behav, cannot be "all")
        """
        search_path = self._join(local_or_remote, experiment_type)
        search_prefix = self.cfg["sub_prefix"] + "*"
        return self._search_for_directories(
            local_or_remote, search_path, search_prefix
        )

    def _search_ses_from_sub_dir(
        self, local_or_remote: str, experiment_type: str, sub: str
    ):
        """
        See _search_subs_from_project_dir(), same but for serching sessions
        within a sub directory.
        """
        search_path = self._join(local_or_remote, [experiment_type, sub])
        search_prefix = self.cfg["ses_prefix"] + "*"
        return self._search_for_directories(
            local_or_remote, search_path, search_prefix
        )

    def _search_for_directories(
        self, local_or_remote: str, search_path: str, search_prefix: str
    ):
        """
        Wrapper to determine the method used to search for search prefix directories
        in the search path.

        :param local_or_remote: "local" or "remote"
        :param search_path: full filepath to search in0
        :param search_prefix: file / dirname to search (e.g. "sub-*")
        """
        if local_or_remote == "remote" and self.cfg["ssh_to_remote"]:

            all_dirnames = self._search_ssh_remote_for_directories(
                search_path, search_prefix
            )
        else:
            all_dirnames = self._search_filesystem_path_for_directorys(
                search_path + "/" + search_prefix
            )
        return all_dirnames

    def _search_filesystem_path_for_directorys(
        self, search_path_with_prefix: str
    ):
        """
        Use glob to search the full search path (including prefix) with glob.
        Files are filtered out of results, returning directories only.
        """
        all_dirnames = []
        for file_or_dir in glob.glob(search_path_with_prefix):
            if os.path.isdir(file_or_dir):
                all_dirnames.append(os.path.basename(file_or_dir))
        return all_dirnames

    def _search_ssh_remote_for_directories(
        self, search_path: str, search_prefix: str
    ):
        """
        Search for the search prefix in the search path over SSH.
        Returns the list of matching directories, files are filtered out.
        """
        with paramiko.SSHClient() as client:
            self._connect_client(client, private_key_path=self._ssh_key_path)

            sftp = client.open_sftp()

            all_dirnames = []
            try:
                for file_or_dir in sftp.listdir_attr(search_path):
                    if stat.S_ISDIR(file_or_dir.st_mode):
                        if fnmatch.fnmatch(
                            file_or_dir.filename, search_prefix
                        ):
                            all_dirnames.append(file_or_dir.filename)
            except FileNotFoundError:
                self._raise_error(f"No file found at {search_path}")

        return all_dirnames

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    @requires_ssh_configs
    def _setup_ssh_key(self):
        """
        Setup an SSH private / public key pair with remote server. First, a private key
        is generated in the appdir. Next a connection requiring input password
        made, and the public part of the key added to ~/.ssh/authorized_keys.
        """
        self._generate_and_write_ssh_key()

        password = getpass.getpass(
            "Please enter password to your remote host to add the public key. "
            "You will not have to enter your password again."
        )

        key = paramiko.RSAKey.from_private_key_file(self._ssh_key_path)

        self._add_public_key_to_remote_authorized_keys(password, key)

    @requires_ssh_configs
    def _verify_ssh_remote_host(self):
        """
        Setup SSH host keys. Display the server RSA key and require user to accept.
        Once accepted, hostkey is stored in appdir for future use with paramiko.
        """
        with paramiko.Transport(self.cfg["remote_host_id"]) as transport:
            transport.connect()
            key = transport.get_remote_server_key()

        self._message_user(
            "The host key is not cached for this server:"
            f" {self.cfg['remote_host_id']}.\nYou have no guarantee that the server is"
            f" the computer you think it is.\nThe server's {key.get_name()} key"
            f" fingerprint is: {key.get_base64()}\nIf you trust this host, to connect"
            " and cache the host key, press y: "
        )
        input_ = input()

        if input_ == "y":
            client = paramiko.SSHClient()
            client.get_host_keys().add(
                self.cfg["remote_host_id"], key.get_name(), key
            )
            client.get_host_keys().save(self._hostkeys)
            sucess = True
        else:
            self._message_user("Host not accepted. No connection made.")
            sucess = False

        return sucess

    def _generate_and_write_ssh_key(self):
        key = paramiko.RSAKey.generate(4096)
        key.write_private_key_file(self._ssh_key_path)

    def _add_public_key_to_remote_authorized_keys(
        self, password: str, key: paramiko.rsakey.RSAKey
    ):
        """
        Append the public part of key to remote server ~/.ssh/authorized_keys.
        """
        with paramiko.SSHClient() as client:
            self._connect_client(client, password=password)

            client.exec_command("mkdir -p ~/.ssh/")
            client.exec_command(
                # double >> for concatenate
                f'echo "{key.get_name()} {key.get_base64()}" >> ~/.ssh/authorized_keys'
            )
            client.exec_command("chmod 644 ~/.ssh/authorized_keys")
            client.exec_command("chmod 700 ~/.ssh/")

        self._message_user(
            f"SSH key pair setup successfully. Private key at: {self._ssh_key_path}"
        )

    def _connect_client(
        self, client, password: str = None, private_key_path: str = None
    ):
        """
        Connect client to remote server using paramiko.
        Accept either password or path to private key, but not both.
        """
        try:
            client.get_host_keys().load(self._hostkeys)
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            client.connect(
                self.cfg["remote_host_id"],
                username=self.cfg["remote_host_username"],
                password=password,
                key_filename=private_key_path,
                look_for_keys=True,
            )
        except Exception:
            self._raise_error("ssh_connection_error")

    # --------------------------------------------------------------------------------------------------------------------
    # Handle Configs
    # --------------------------------------------------------------------------------------------------------------------

    def _save_cfg_to_configs_file(self):
        """
        Save self.cfg to appdir configuration .yaml file.
        Path objects must be converted to string (and likewise, back to Path when loaded).
        """
        cfg_to_save = copy.deepcopy(self.cfg)
        self._convert_str_and_pathlib_paths(cfg_to_save, "path_to_str")
        self._dump_configs_to_file(cfg_to_save)

    def _dump_configs_to_file(self, config_dict):
        with open(self._config_path, "w") as config_file:
            yaml.dump(config_dict, config_file, sort_keys=False)

    def _config_file_exists(self, prompt_on_fail: bool) -> bool:
        """
        Check the config file exists in the expected directory.

        :param prompt_on_fail: if config file not found, warn the user.

        :return: True or False
        """
        exists = os.path.isfile(self._config_path)

        if not exists and prompt_on_fail:
            warnings.warn(
                "Configuration file has not been initialized. "
                "Use make_config_file() to setup before continuing."
            )

        return exists

    def _attempt_load_configs(self, prompt_on_fail: bool) -> Union[bool, dict]:
        """
        Attempt to load the config file. If it does not exist or crashes
        when attempt to load from file, return False.

        :param prompt_on_fail: if config file not found, or crashes on load,
                               warn the user.

        :return: loaded dictionary, or False if not loaded.
        """
        if not self._config_file_exists(prompt_on_fail):
            return False

        try:
            with open(self._config_path, "r") as config_file:
                config_dict = yaml.full_load(config_file)

            self._convert_str_and_pathlib_paths(config_dict, "str_to_path")

        except Exception:
            config_dict = False

            if prompt_on_fail:
                self._message_user(
                    "Config file failed to load. Check file formatting at"
                    f" {self._config_path}. If cannot load, re-initialise configs with"
                    " make_config_file()"
                )

        return config_dict

    def _convert_str_and_pathlib_paths(
        self, config_dict: dict, direction: str
    ):
        """
        Config paths are stored as str in the .yaml but used as Path
        in the module, so make the conversion here.

        :param config_dict: self.cfg dict of configs
        :param direction: "path_to_str" or "str_to_path"
        """
        for path_key in ["local_path", "remote_path"]:
            if direction == "str_to_path":
                config_dict[path_key] = Path(config_dict[path_key])
            elif direction == "path_to_str":
                config_dict[path_key] = config_dict[path_key].as_posix()
            else:
                self._raise_error(
                    "Option must be 'path_to_str' or 'str_to_path'"
                )

    def _get_experiment_type_items(self, experiment_type):
        """
        Get the .items() structure of the data type, either all of
        them (stored in self._ses_dirs or a single item.
        """
        return (
            zip([experiment_type], [self._ses_dirs[experiment_type]])
            if experiment_type != "all"
            else self._ses_dirs.items()
        )

    # --------------------------------------------------------------------------------------------------------------------
    # Utils TODO: move where possible
    # --------------------------------------------------------------------------------------------------------------------

    def _join(self, base: str, subdirs: Union[str, list]):
        """
        Function for joining relative path to base dir. If path already
        starts with base dir, the base dir will not be joined.

        :param base: "local", "remote" or "appdir"
        :param subdirs: a list (or string for 1) of directory names to be joined into a path.
                           If file included, must be last entry (with ext).
        """
        if isinstance(subdirs, list):
            subdirs_str = "/".join(subdirs)
        else:
            subdirs_str = cast(str, subdirs)

        subdirs_path = Path(subdirs_str)

        base_dir = self._get_base_dir(base)

        if self._path_already_stars_with_base_dir(base_dir, subdirs_path):
            joined_path = subdirs_path
        else:
            joined_path = base_dir / subdirs_path

        return joined_path.as_posix()

    def _get_base_dir(self, base):
        """
        Convenience function to return the full base path.
        """
        if base == "local":
            base_dir = self.cfg["local_path"]
        elif base == "remote":
            base_dir = self.cfg["remote_path"]
        elif base == "appdir":
            base_dir = self._get_user_appdir_path()
        return base_dir

    def _path_already_stars_with_base_dir(self, base_dir: Path, path_: Path):
        return path_.as_posix().startswith(base_dir.as_posix())

    def _process_names(self, names: Union[list, str], sub_or_ses: str):
        """
        Check a single or list of input session or subject names. First check the type is correct,
        next prepend the prefix sub- or ses- to entries that do not have the relevant prefix. Finally,
        check for duplicates.

        :param names: str or list containing sub or ses names (e.g. to make dirs)
        :param sub_or_ses: "sub" or "ses" - this defines the prefix checks.
        """
        if type(names) not in [str, list] or any(
            [not isinstance(ele, str) for ele in names]
        ):
            self._raise_error(
                "Ensure subject and session names are list of strings, or string"
            )
            return False

        if isinstance(names, str):
            names = [names]

        prefix = self._get_sub_or_ses_prefix(sub_or_ses)
        prefixed_names = self._ensure_prefixes_on_list_of_names(names, prefix)

        if len(prefixed_names) != len(set(prefixed_names)):
            self._raise_error(
                "Subject and session names but all be unqiue (i.e. there are no"
                " duplicates in list input)"
            )

        return prefixed_names

    def _get_sub_or_ses_prefix(self, sub_or_ses: str):
        if sub_or_ses == "sub":
            prefix = self.cfg["sub_prefix"]
        elif sub_or_ses == "ses":
            prefix = self.cfg["ses_prefix"]
        return prefix

    def _get_user_appdir_path(self):
        """
        It is not possible to write to programfiles in windows from app without admin permissions
        However if admin permission given drag and drop dont work, and it is not good practice.
        Use appdirs module to get the AppData cross-platform and save / load all files form here .
        """
        base_path = Path(
            os.path.join(
                appdirs.user_data_dir("ProjectManagerSWC"), self.project_name
            )
        )

        if not os.path.isdir(base_path):
            os.makedirs(base_path)

        return base_path

    def _check_experiment_type_is_valid(self, experiment_type, prompt_on_fail):
        """
        Check the user-passed data type is valid (must be a key on self.ses_dirs or "all"
        """
        is_valid = (
            experiment_type in self._ses_dirs.keys()
            or experiment_type == "all"
        )

        if prompt_on_fail and not is_valid:
            self._message_user(
                f"experiment_type: '{experiment_type}' is not valid. Must be one of"
                f" {list(self._ses_dirs.keys())}. No directories were made."
            )

        return is_valid

    def _raise_error(self, message: str):
        """
        Temporary centralized way to raise and error
        """
        if message == "ssh_connection_error":
            message = (
                "Could not connect to server. Ensure that \n1) You are on SWC network"
                f" / VPN. \n2) The remote_host_id: {self.cfg['remote_host_id']} is"
                " correct.\n3) The remote username:"
                f" {self.cfg['remote_host_username']}, and password are correct."
            )
        raise BaseException(message)

    @staticmethod
    def _message_user(message: str):
        """
        Temporary centralised way to message user.
        """
        print(message)

    @staticmethod
    def _make_dirs(paths: Union[str, list]):
        """
        For path or list of path, make them if do not already exist.
        """
        if isinstance(paths, str):
            paths = [paths]

        for path_ in paths:
            if not os.path.isdir(path_):
                os.makedirs(path_)
            else:
                warnings.warn(
                    "The following directory was not made because it already exists"
                    f" {path_}"
                )

    @staticmethod
    def _ensure_prefixes_on_list_of_names(names, prefix):
        """ """
        n_chars = len(prefix)
        return [
            prefix + name if name[:n_chars] != prefix else name
            for name in names
        ]
