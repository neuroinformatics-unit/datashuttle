from types import SimpleNamespace
import os
import appdirs
import getpass
import paramiko
import yaml
import warnings
from pathlib import Path
from typing import Union
import copy
from ftpsync.ftp_target import FTPTarget
from ftpsync.sftp_target import SFTPTarget
from ftpsync.targets import FsTarget
from ftpsync.synchronizers import UploadSynchronizer, DownloadSynchronizer
from functools import wraps
import fnmatch
import stat
import glob

# TODO

# 1) setup SSH key in windows, mac, linux
# 2) ssh to remote server
# 3) transfer file
# 4) checks
# TODO: need to setup different users for ssh key / test multiple users

# TODO
# add ssh single folder
# add
# Tree to walk through entire directory tree
# TODO: add function for upload syncronise within project
#       add function for general upload (not in standard folder setup)
#       add download function
#       think hard - is there any other function to implement?
#       doc, refactor, type
#       talk to Adam, write tests
#       CLI, GUI
#       test pysync fork
# TODO: going to need to print all instances where a file was not moved because already exists.
# populate remote by syncing only... otherwise confusing to populate on remote from local. If want
# full file tree can go to remote and set it up there
# test breaking the internet connection mid-up / download
# Assumptions: the remote host is unix system
# TODO: add info file for each ses with date time etc.

# TODO:
# - typing
# - print is currently used to feedback information, improve
# - logging
# - mounted network drive not supported
# - 'generate bids filename name'
# - (partial - check) allow different profiles on the same system by passing the username to the class rather than loading from config
# - handling the configs is a little circlar ATM as if fail, set_config_path loads them back into the class, might be easier to extract make_config_file() to separate loading class / function
#   but it is less neat for the user.


# filter files and folders
# return

# filter out files.

# TODO: completely different procedure if it is not local

# handle all
# handle if data type not selected / file not found
# handle upload vs download versions

# --------------------------------------------------------------------------------------------------------------------
# Folder Class
# --------------------------------------------------------------------------------------------------------------------


class Folder():
    def __init__(self, name, used, subfolders=None):
        self.name = name
        self.used = used
        self.subfolders = subfolders

# --------------------------------------------------------------------------------------------------------------------
# Class Decorators
# --------------------------------------------------------------------------------------------------------------------

def requires_ssh_configs(func):
    """
    Decorator to check file is loaded. Used on Mainwindow class methods only as first arg is assumed to be self (containing cfgs)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if (not args[0].cfg["remote_host_id"] or not args[0].cfg["remote_host_username"]):
            args[0]._raise_error("Cannot setup SSH connection, configuration file remote_host_id or remote_host_username is not set.")
        else:
            func(*args, **kwargs)

    return wrapper

# --------------------------------------------------------------------------------------------------------------------
# Project Manager Class
# --------------------------------------------------------------------------------------------------------------------

class ProjectManager():
    """
    """
    def __init__(self, username):

        self.username = username

        self._config_path = self._join("appdir", "config.yaml")
        self.cfg = self._attempt_load_configs(prompt_on_fail=True)

        if self.cfg:
            self._ssh_key_path = None
            self._ses_folders = None

            if self.cfg:
                self.set_attributes_after_config_load()

    def set_attributes_after_config_load(self):
        """
        Once config file is loaded, update all private attributes according to config contents.

        The _ses_folders contains the entire directory tree for each data type. The structure is that the top-level folder (e.g. ephys,
        behav, microscopy) are found in the project root. Then sub- and ses- folders are created in this project root, and all subfolders
        are created at the session level.

        TODO: - for adding new files, first this tree but be extended, then a new option added to inputs of make_config file. This can be
                refactored and an easier way to indicate the relationship between folders found.
              - factor out _ses_folders generation
              - decide whether to repeat top-level dir name in the session level dir
        """
        self._ssh_key_path = self._join("appdir", self.username + "_ssh_key")
        self._hostkeys = self._join("appdir", "hostkeys")

        self._ses_folders = {"ephys": Folder("ephys",
                                             self.cfg["use_ephys"],
                                             subfolders={"ephys_behav": Folder("behav",
                                                                               self.cfg["use_ephys_behav"],
                                                                               subfolders={"ephys_behav_camera": Folder("camera",
                                                                                                                        self.cfg["use_ephys_behav_camera"],
                                                                                                                        ),
                                                                                           },
                                                                               ),
                                                         },
                                             ),

                             "behav": Folder("behav",
                                             self.cfg["use_behav"],
                                             subfolders={"behav_camera":
                                                             Folder("camera",
                                                                    self.cfg["use_behav_camera"]
                                                                    ),
                                                         },
                                             ),

                             "microscopy": Folder("microscopy",
                                                  self.cfg["use_microscopy"],
                                                  ),
                             }

# --------------------------------------------------------------------------------------------------------------------
# Publicly Accessible Directory Makers
# --------------------------------------------------------------------------------------------------------------------

    def make_sub_folder(self,
                        data_type: str,
                        sub_names: Union[str, list],
                        ses_names: Union[str, list] = None,
                        make_ses_tree: bool = True):
        """
        Make a subject directory in the data type folder. By default, it will create the entire directory tree for this subject.

        See _make_directory_tree() for inputs.
        """
        sub_names = self._process_names(sub_names, "sub")

        if make_ses_tree:
            if ses_names is None:
                ses_names = [self.cfg["ses_prefix"] + "001"]  # TODO: default ses name
            else:
                ses_names = self._process_names(ses_names, "ses")
        else:
            ses_names = []

        self._make_directory_trees(data_type, sub_names, ses_names, make_ses_tree, process_names=False)

    def make_ses_folder(self,
                        data_type: str,
                        sub_names: Union[str, list],
                        ses_names: Union[str, list],
                        make_ses_tree: bool = True):
        """
        See _make_directory_tree() for inputs.
        """
        self._make_directory_trees(data_type, sub_names, ses_names, make_ses_tree)

    def make_ses_tree(self,
                      data_type: str,
                      sub_names: Union[str, list],
                      ses_names: Union[str, list]):
        """
        See _make_directory_tree() for inputs.
        """
        self._make_directory_trees(data_type, sub_names, ses_names)

# --------------------------------------------------------------------------------------------------------------------
# Make Directory Trees
# --------------------------------------------------------------------------------------------------------------------

    def _make_directory_trees(self,
                              data_type: str,
                              sub_names: Union[str, list],
                              ses_names: Union[str, list],
                              make_ses_tree: bool = True,
                              process_names: bool = True):
        """
        Entry method to make a full directory tree. It will iterate through all
        passed subjects, then sessions, then subfolders within a data_type folder. This
        permits flexible creation of folders (e.g. to make subject only, do not pass session name.

        subject and session names are first processed to ensure correct format.

        :param data_type:       The data_type to make the folder in (e.g. "ephys", "behav", "microscopy"). If "all" is selected,
                                folder will be created for all data type.
        :param sub_names:       subject name / list of subject names to make within the folder (if not already, these will be prefixed with sub/ses identifier)
        :param ses_names:       session names (same format as subject name). If no session is provided, defaults to "ses-001".
        :param make_ses_tree:   option to make the entire session tree under the subject directory. If False, the subject folder only will be created.
        :param process_names:   option to process names or not (e.g. if names were processed already).

        """
        sub_names = self._process_names(sub_names, "sub") if process_names else sub_names
        ses_names = self._process_names(ses_names, "ses") if process_names else ses_names

        if not self._check_data_type_is_valid(data_type, prompt_on_fail=True):
            return

        data_type_items = self._get_data_type_items(data_type)

        for data_type_key, data_type_dir in data_type_items:

            if data_type_dir.used:
                self._make_dirs(self._join("local", data_type_dir.name))

                for sub in sub_names:

                    self._make_dirs(self._join("local", [data_type_dir.name, sub]))

                    for ses in ses_names:

                        self._make_dirs(self._join("local", [data_type_dir.name, sub, ses]))

                        if make_ses_tree:
                            self._make_ses_directory_tree(sub, ses, data_type_key)

    def _make_ses_directory_tree(self,
                                 sub: str,
                                 ses: str,
                                 data_type_key: str):
        """
        Make the directory tree within a session. This is dependent on the data_type (e.g. "ephys")
        folder and defined in the subfolders field on the Folder class, in self._ses_folders.

        All subfolders will be make recursively, unless the .used attribute on the Folder class is
        False. This will also stop and subfolders of the subfolder been created.

        :param sub:              subject name to make directory tree in
        :param ses:              session name to make directory tree in
        :param data_type_key:    data_type_key (e.g. "ephys") to make directory tree in. Note this defines the subfolders created.
        """
        data_type_dir = self._ses_folders[data_type_key]

        if data_type_dir.used and data_type_dir.subfolders:
            self._recursive_make_subfolders(folder=data_type_dir,
                                            path_to_folder=[data_type_dir.name, sub, ses])

    def _recursive_make_subfolders(self,
                                   folder: type[Folder],
                                   path_to_folder: list):
        """
        Function to recursively create all directories in a Folder .subfolders field.

        i.e. this will first create a folder based on the .name attribute. It will then
        loop through all .subfolders, and do the same - recursively looping through subfolders
        until the entire directory tree is made. If .used attribute on a folder is False,
        that folder and all subfolders of the folder will not be made.

        :param folder:
        :param path_to_folder:
        :return:
        """
        if folder.subfolders:

            for subfolder in folder.subfolders.values():

                if subfolder.used:
                    new_path_to_folder = path_to_folder + [subfolder.name]
                    self._make_dirs(self._join("local", new_path_to_folder))
                    self._recursive_make_subfolders(subfolder, new_path_to_folder)

# --------------------------------------------------------------------------------------------------------------------
# File Transfer Public (TODO)
# --------------------------------------------------------------------------------------------------------------------

    def upload_data(self, data_type, sub_names, ses_names):  # TODO: this is going to be very sub-optimal as keep opening server. Maybe it is better to use the MATCH / ETC Filtering. This really is sub-optimal for ssh, ssh every time to search sub folder for ses...
        """"""
        self._transfer_sub_ses_data("upload", data_type, sub_names, ses_names)

    def download_data(self):
        """"""
        self._transfer_sub_ses_data("download", data_type, sub_names, ses_names)

    def _transfer_sub_ses_data(self, upload_or_download, data_type, sub_names, ses_names):  # TODO: fix naming
        """"""
        folder_to_search = "local" if upload_or_download == "upload" else "remote"

        data_type_items = self._get_data_type_items(data_type)

        for data_type_key, data_type_dir in data_type_items:  # TODO: do that key is canonical while .name is user name

            if sub_names != "all":  # TODO: own function? line?
                sub_names = self._process_names(sub_names, "sub")
            else:
                sub_names = self._search_subs_from_project_folder(folder_to_search, data_type_key)  # TODO: change local vs remote

            for sub in sub_names:

                if ses_names != "all":  # TODO: own function? line?
                    ses_names = self._process_names(ses_names, "ses")
                else:
                    ses_names = self._search_ses_from_sub_folder(folder_to_search, data_type_key, sub)  # TODO: change local vs remote

                for ses in ses_names:

                    filepath = os.path.join(data_type_dir.name, sub, ses)
                    self._move_folder_or_file(filepath, upload_or_download, preview=False)

    # --------------------------------------------------------------------------------------------------------------------
    # Handle "all" flag and search for all sub and ses
    # --------------------------------------------------------------------------------------------------------------------

    def _search_subs_from_project_folder(self, local_or_remote, data_type):  # TODO: change name! not from filesystem!
            """"""
            search_path = self._join(local_or_remote, data_type)
            search_prefix = self.cfg["sub_prefix"] + "*"
            return self._search_for_directories(local_or_remote, search_path, search_prefix)

    def _search_ses_from_sub_folder(self, local_or_remote, data_type, sub):  # TODO: change name! not from filesystem!
        """"""
        search_path = self._join(local_or_remote, [data_type, sub])
        search_prefix = self.cfg["ses_prefix"] + "*"
        return self._search_for_directories(local_or_remote, search_path, search_prefix)

    def _search_for_directories(self, local_or_remote, search_path, search_prefix):
        """"""
        if local_or_remote == "remote" and self.cfg["ssh_to_remote"]:
            all_foldernames = self._search_ssh_remote_for_directories(search_path, search_prefix)  # use Pathlib? TODO: come to some conclusion on this... (i.e. allwasy use path? str? etc messy ATM
        else:
            all_foldernames = self._search_filesystem_path_for_directorys(search_path + "/" + search_prefix)
        return all_foldernames

    def _search_filesystem_path_for_directorys(self, search_path):
        """"""
        all_foldernames = []
        for file_or_folder in glob.glob(search_path):
            if os.path.isdir(file_or_folder):
                all_foldernames.append(os.path.basename(file_or_folder))
        return all_foldernames

    def _search_ssh_remote_for_directories(self, search_path, search_prefix):
        """
        https://stackoverflow.com/questions/12295551/how-to-list-all-the-folders-and-files-in-the-directory-after-connecting-through
        """
        with paramiko.SSHClient() as client:
            self._connect_client(client, private_key=self._ssh_key_path)

            sftp = client.open_sftp()

            all_foldernames = [] # TODO: not just filenames
            try:
                for file_or_folder in sftp.listdir_attr(search_path):  # TODO: own function, utils
                    if stat.S_ISDIR(file_or_folder.st_mode):
                        if fnmatch.fnmatch(file_or_folder.filename, search_prefix):
                            all_foldernames.append(file_or_folder.filename)
            except FileNotFoundError:
                self._raise_error((f"No file found at {search_path}"))

        return all_foldernames

# --------------------------------------------------------------------------------------------------------------------
# File Transfer Private (TODO)
# --------------------------------------------------------------------------------------------------------------------

    def upload_project_folder_or_file(self, filepath, upload, preview=False):
        """
        TODO: currently everything is relative to base path. Do we ever want to let people provide full filepath?
        """
        self._move_folder_or_file(filepath, "upload", preview)

    def download_project_folder_or_file(self, filepath, preview=False):
        """
        """
        self._move_folder_or_file(filepath, "download", preview)

    def _move_folder_or_file(self, filepath, upload_or_download, preview):
        """"""
        local_filepath = self._join("local", filepath)
        remote_filepath = self._join("remote", filepath)  # TODO: function that checks if the leading path is already provided? yes...

        local = FsTarget(local_filepath)
        remote = self._get_remote_target(remote_filepath)

        opts = self._get_default_upload_opts(preview)

        syncronizer = self._get_syncronizer(upload_or_download)
        s = syncronizer(local, remote, opts)
        s.run()

    def _get_syncronizer(self, upload_or_download):
        """"""
        if upload_or_download == "upload":
            syncronizer = UploadSynchronizer

        elif upload_or_download == "download":
            syncronizer = DownloadSynchronizer

        return syncronizer

    def _get_remote_target(self, remote_filepath):
        """
        """
        if self.cfg["ssh_to_remote"]:  # TODO: own function

            remote = SFTPTarget(remote_filepath,
                                self.cfg["remote_host_id"],
                                username=self.cfg["remote_host_username"],
                                private_key=self._ssh_key_path,
                                hostkeys=self._hostkeys)

        else:
            remote = FsTarget(remote_filepath)

        return remote

    def _get_default_upload_opts(self, preview):
        """
        """
        opts = {"help": False,
                "verbose": 5,
                "quiet": 0,
                "debug ": False,
                "case": "strict",
                "dry_run": preview,
                "progress": False,  # TODO
                "no_color": True,
                "ftp_active": False,  # TODO
                "migrate": False,
                "no_verify_host_keys": False,
                #                "match": 3,
                #                "exclude": 3,
                "prompt": False,
                "no_prompt": False,
                "no_keyring": True,
                "no_netrc": True,
                "store_password": False,
                "force": "restore",  # False
                "resolve": "ask",
                "delete": False,
                "delete_unmatched": False,
                "create_folder": True,
                "report_problems": False,
                }
        return opts

# --------------------------------------------------------------------------------------------------------------------
# SSH
# --------------------------------------------------------------------------------------------------------------------

    @requires_ssh_configs
    def setup_ssh_connection_to_remote_server(self):

        verified = self.verify_ssh_remote_host()

        if verified:
            self.setup_ssh_key()

    @requires_ssh_configs
    def setup_ssh_key(self):
        """generate_ssh_key_and_copy_pub_to_remote_host"""
        # TODO: checks that these dont already exist.
        # TODO: setup method for local connection (not ssh - check host path)
        # TODO: logging
        # TODO: no password on key atm, doesn't really work if want to sync (I think)
        self._generate_and_write_ssh_key()  # TODO: this does not freeze process, add a quick message?

        password = getpass.getpass("Please enter password to your remote host to add the public key. "
                                   "You will not have to enter your password again.")

        key = paramiko.RSAKey.from_private_key_file(self._ssh_key_path)

        self._add_public_key_to_remote_authorized_keys(password, key)

    @requires_ssh_configs
    def verify_ssh_remote_host(self):
        """"""
        with paramiko.Transport(self.cfg["remote_host_id"]) as transport:
            transport.connect()
            key = transport.get_remote_server_key()

        self._message_user(f"The host key is not cached for this server: {self.cfg['remote_host_id']}.\n"
                           f"You have no guarantee that the server is the computer you think it is.\n"
                           f"The server's {key.get_name()} key fingerprint is: {key.get_base64()}\n"
                           f"If you trust this host, to connect and cache the host key, press y: ")
        input_ = input()

        if input_ == "y":
            client = paramiko.SSHClient()
            client.get_host_keys().add(self.cfg["remote_host_id"], key.get_name(), key)
            client.get_host_keys().save(self._hostkeys)
            set = True
        else:
            self._message_user("Host not accepted. No connection made.")
            set = False

        return set

    def write_public_key(self, filepath, key):
        """
        TODO: should this be done automatically, or just provided in case user wants public key? Paramiko can use the private key only.
        """
        key = paramiko.RSAKey.from_private_key_file(self._ssh_key_path)

        with open(filepath, "w") as public:
            public.write(key.get_base64())
        public.close()

    def _generate_and_write_ssh_key(self):
        """"""
        key = paramiko.RSAKey.generate(4096)
        key.write_private_key_file(self._ssh_key_path)

    def _add_public_key_to_remote_authorized_keys(self, password, key):
        """ssh-copy-id but from any platform.Could be improved (i.e. use ssh-copy-id if possible / there is a python version for windows"""
        with paramiko.SSHClient() as client:

            self._connect_client(client, password=password)

            client.exec_command("mkdir -p ~/.ssh/")  # not used ssh-copy-id as platform independent # TODO: check that formatting is the same as ssh-copy-id
            client.exec_command(f'echo "{key.get_name()} {key.get_base64()}" >> ~/.ssh/authorized_keys')  # double >> for concatenate
            client.exec_command("chmod 644 ~/.ssh/authorized_keys")
            client.exec_command("chmod 700 ~/.ssh/")

        self._message_user(f"SSH key pair setup successfully. Private key at: {self._ssh_key_path}")

    def _connect_client(self, client, password=None, private_key=None):  # TODO: private key name
        try:
            client.get_host_keys().load(self._hostkeys)
            client.set_missing_host_key_policy(paramiko.RejectPolicy())  # TODO ######################
            client.connect(self.cfg["remote_host_id"], username=self.cfg["remote_host_username"], password=password, key_filename=private_key, look_for_keys=True)
        except:
            self._raise_error("ssh_connection_error")

# --------------------------------------------------------------------------------------------------------------------
# Handle Configs
# --------------------------------------------------------------------------------------------------------------------

    def make_config_file(self,
                         local_path: str,
                         remote_path: str,
                         ssh_to_remote: bool,
                         remote_host_id: str = None,  # TODO: use Optional
                         remote_host_username: str = None,
                         sub_prefix: str = "sub-",
                         ses_prefix: str = "ses-",
                         use_ephys: bool = True,
                         use_ephys_behav: bool = True,
                         use_ephys_behav_camera: bool = True,
                         use_behav: bool = True,
                         use_behav_camera: bool = True,
                         use_microscopy: bool = True
                         ):
        """
        Initialise a config file for using the project manager on the local system. Once initialised, these
        settings will be used each time the project manager is opened.

        :param local_path:                  path to project folder on local machine
        :param remote_path:                 path to project folder on remote machine. Note this cannot
                                            include ~ home directory syntax, must contain the full path (e.g. /nfs/nhome/live/jziminski)
        :param ssh_to_remote                if true, ssh will be used to connect to remote cluster and remote_host_id, remote_host_username must be provided.
        :param remote_host_id:              path to remote machine root, either path to mounted drive (TODO: CURRENTLY NOT SUPPORTED) or address for host for ssh
        :param remote_host_username:        username for which to login to remote host.
        :param sub_prefix:                  prefix for all subject (i.e. mouse) level directory. Default is BIDS: "sub-"
        :param ses_prefix:                  prefix for all session level directory. Default is BIDS: "ses-"
        :param use_ephys:                   setting true will create ephys directory tree on this machine
        :param use_ephys_behav:             setting true will create behav directory in ephys directory on this machine
        :param use_ephys_behav_camera:      setting true will create camera directory in ephys behaviour directory on this machine
        :param use_behav:                   setting true will create behav directory
        :param use_behav_camera:            setting true will create camera directory in behav directory
        :param use_microscopy:              settin true will create microscope directory
        :return: None

        NOTE: higher level folder settings will override lower level settings (e.g. if ephys_behav_camera=True and ephys_behav=False,
              ephys_behav_camera will not be made).

        TODO: - this does not currently consider file levels (e.g. behav > camera file structure).
              - check if already exists, if so throw a overwrite warning
              - mounted network drive not supported
              - perform checks on inputs
        """
        # TODO: refactor to own function
        if remote_path[0] == "~":
            self._raise_error("remote_path must contain the full directory path with no ~ syntax")

        if ssh_to_remote is True and (not remote_host_id or not remote_host_username):
            self._raise_error("ssh to remote set but no remote_host_id or remote_host_username not provided")

        if ssh_to_remote is False and (remote_host_id or remote_host_username):
            warnings.warn("SSH to remote is false, but remote_host_id or remote_host_username provided")

        config_dict = {
            "local_path": local_path,
            "remote_path": remote_path,
            "ssh_to_remote": ssh_to_remote,
            "remote_host_id": remote_host_id,
            "remote_host_username": remote_host_username,
            "sub_prefix": sub_prefix,
            "ses_prefix": ses_prefix,
            "use_ephys": use_ephys,
            "use_ephys_behav": use_ephys_behav,
            "use_ephys_behav_camera": use_ephys_behav_camera,
            "use_behav": use_behav,
            "use_behav_camera": use_behav_camera,
            "use_microscopy": use_microscopy,
        }

        self._dump_configs_to_file(config_dict)

        self.cfg = self._attempt_load_configs(prompt_on_fail=False)
        self.set_attributes_after_config_load()
        self._message_user("Configuration file has been saved and options loaded into the project manager.")

    def update_config(self, option_key, new_info):
        """"""
        if option_key in ["local_path", "remote_path"]:  # TODO: move to init  # TODO: some duplicate of _convert_str_and_pathlib_paths
            new_info = Path(new_info)

        self.cfg[option_key] = new_info
        self.set_attributes_after_config_load()
        self._save_cfg_to_configs_file()

    def _save_cfg_to_configs_file(self):
        """"""
        cfg_to_save = copy.deepcopy(self.cfg)
        self._convert_str_and_pathlib_paths(cfg_to_save,
                                            "path_to_str")
        self._dump_configs_to_file(cfg_to_save)

    def _dump_configs_to_file(self, config_dict):
        """"""
        with open(self._config_path, "w") as config_file:
            yaml.dump(config_dict, config_file, sort_keys=False)

    def _config_file_exists(self, prompt_on_fail: bool) -> bool:
        """
        Check the config file exists in the expected directory.

        :param prompt_on_fail: if config file not found, warn the user.

        :return: True or False
        """
        exists = os.path.isfile(self._config_path)  # TODO: could make own var

        if not exists and prompt_on_fail:
            warnings.warn("Configuration file has not been initialed. Use make_config_file() to setup before continuing.")

        return exists

    def _attempt_load_configs(self, prompt_on_fail: bool) -> Union[bool, dict]:
        """
        Attempt to load the config file. If it does not exist or crashes when attempt to load from file, return False.

        :param prompt_on_fail: if config file not found, or crashes on load, warn the user.

        :return: loaded dictionary, or False if not loaded.
        """
        if not self._config_file_exists(prompt_on_fail):
            return False

        try:
            with open(self._config_path, "r") as config_file:
                config_dict = yaml.full_load(config_file)

            self._convert_str_and_pathlib_paths(config_dict, "str_to_path")

        except:
            config_dict = False

            if prompt_on_fail:
                self._message_user(f"Config file failed to load. Check file formatting at {self._config_path}. "
                                   f"If cannot load, re-initialise configs with make_config_file()")

        return config_dict

    def _convert_str_and_pathlib_paths(self, config_dict, direction):
        """"""
        for path_key in ["local_path", "remote_path"]:  # TODO: move to init
            if direction == "str_to_path":
                config_dict[path_key] = Path(config_dict[path_key])
            elif direction == "path_to_str":
                config_dict[path_key] = config_dict[path_key].as_posix()
            else:
                self._raise_error("Option must be 'path_to_str' or 'str_to_path'")

    def _get_data_type_items(self, data_type):
        return zip([data_type], [self._ses_folders[data_type]]) if data_type != "all" else self._ses_folders.items()

# --------------------------------------------------------------------------------------------------------------------
# Public Getters
# --------------------------------------------------------------------------------------------------------------------

    def get_local_path(self):
        return self.cfg["local_path"].as_posix()

    def get_appdir_path(self):
        return self._get_user_appdir_path().as_posix()

    def get_remote_path(self):
        return self.cfg["remote_path"].as_posix()

# --------------------------------------------------------------------------------------------------------------------
# Utils TODO: move where possible
# --------------------------------------------------------------------------------------------------------------------

    def _join(self, base, subfolders):  # list or string
        """
        TODO: this function is kind of messy now, and goes str / list > Path > str...
        will not add if path already starts with
        """
        if type(subfolders) == list:  # TODO: own function, this ins't very neat
            subfolders = "/".join(subfolders)

        subfolders = Path(subfolders)

        if base == "local":  # cannot use dict as paths not defined before cfg loaded, TODO: own function
            base_dir = self.cfg["local_path"]
        elif base == "remote":
            base_dir = self.cfg["remote_path"]
        elif base == "appdir":
            base_dir = self._get_user_appdir_path()

        if self.path_already_stars_with_base_dir(base_dir, subfolders):
            joined_path = subfolders
        else:
            joined_path = base_dir / subfolders

        return joined_path.as_posix()

    def path_already_stars_with_base_dir(self, base_dir, path_):
        """ note Path(x) where x is already a Path object does not cause error TODO: type"""
        return path_.as_posix().startswith(base_dir.as_posix())

    def _process_names(self, names, sub_or_ses):
        """"""
        if type(names) not in [str, list] or any([type(ele) != str for ele in names]):  # TODO: tidy up, decide whether to handle non-str types
            self._raise_error("Ensure subject and session names are list of strings, or string")
            return False

        if type(names) == str:
            names = [names]

        prefix = self._get_sub_or_ses_prefix(sub_or_ses)
        prefixed_names = self._ensure_prefixes_on_list_of_names(names, prefix)

        if len(prefixed_names) != len(set(prefixed_names)):
            self._raise_error("Subject and session names but all be unqiue (i.e. there are no duplicates in list input)")

        return prefixed_names

    def _get_sub_or_ses_prefix(self, sub_or_ses):
        """
        TODO
        """
        if sub_or_ses == "sub":
            prefix = self.cfg["sub_prefix"]
        elif sub_or_ses == "ses":
            prefix = self.cfg["ses_prefix"]
        return prefix

    def _get_user_appdir_path(self):
        """
        Iti s not possible to write to programfiles in windows from app without admin permissions
        However if admin permission given drag and drop dont work, and it is not good practice.
        Use appdirs module to get the AppData cross-platform and save / load all files form here .
        """
        base_path = Path(appdirs.user_data_dir(self.username, "ProjectManagerSWC"))  # name need to match nsis?
        if not os.path.isdir(base_path):
            os.makedirs(base_path)
        return base_path

    def _check_data_type_is_valid(self, data_type, prompt_on_fail):

        is_valid = (data_type in self._ses_folders.keys() or data_type == "all")

        if prompt_on_fail and not is_valid:
            self._message_user(f"data_type: '{data_type}' is not valid. Must be one of {list(self._ses_folders.keys())}. No folders were made.")  # TODO: warning?

        return is_valid

    def _raise_error(self, message):
        """ TODO: custom exception classes? """
        # TODO
        if message == "ssh_connection_error":
            message = f"Could not connect to server. Ensure that \n" \
                      f"1) You are on SWC network / VPN. \n" \
                      f"2) The remote_host_id: {self.cfg['remote_host_id']} is correct.\n" \
                      f"3) The remote username: {self.cfg['remote_host_username']}, and password are correct." \

        raise BaseException(message)

    @staticmethod
    def _message_user(message):
        """ TODO: decide best way to message user based on application (GUI etc.)"""
        print(message)

    @staticmethod
    def _make_dirs(paths):
        """"""
        if type(paths) == str:
            paths = [paths]

        for path_ in paths:
            if not os.path.isdir(path_):
                os.makedirs(path_)
            else:
                warnings.warn(f"The following folder was not made because it already exists {path_}")

    @staticmethod
    def _ensure_prefixes_on_list_of_names(names, prefix):
        """"""
        n_chars = len(prefix)
        return [prefix + name if name[:n_chars] != prefix else name for name in names]
