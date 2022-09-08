from types import SimpleNamespace
import os
import appdirs
import getpass
import paramiko
import yaml
import warnings
from pathlib import Path
from typing import Union

# Assumptions: the remote host is unix system

# TODO:
# - typing
# - print is currently used to feedback information, improve
# - logging
# - mounted network drive not supported

# --------------------------------------------------------------------------------------------------------------------
# Folder Class
# --------------------------------------------------------------------------------------------------------------------


class Folder():
    def __init__(self, name, used, subfolders=None):
        self.name = name
        self.used = used
        self.subfolders = subfolders

    # --------------------------------------------------------------------------------------------------------------------
    # Project Manager Class
    # --------------------------------------------------------------------------------------------------------------------


class ProjectManager():
    """
    TODO: allow different profiles on the same system by passing the username to the class rather than loading from config
    TODO: handling the configs is a little circlar ATM as if fail, set_config_path loads them back into the class, might be easier to extract make_config_file() to separate loading class / function
          but it is less neat for the user.
    """

    def __init__(self, username):

        self.username = username

        self._config_path = self._join("appdir", "config.yaml")
        self.cfg = self._attempt_load_configs(prompt_on_fail=True)

        if self.cfg:

            self._username_ssh_key = None
            self._ses_folders = None

            if self.cfg:
                self.set_attributes_after_config_load()

    def set_attributes_after_config_load(self):
        """
        Once config file is loaded, update all private attributes according to config contents.

        TODO: for adding new files, first this tree but be extended, then a new option added to inputs of make_config file. Can be neatened.
        """
        self._username_ssh_key = self.username + "_ssh_key"

        self._ses_folders = {"ephys": Folder("ephys",
                                             self.cfg.use_ephys,
                                             subfolders={"ephys_behav": Folder("behav",
                                                                                self.cfg.use_ephys_behav,
                                                                                subfolders={"ephys_behav_camera": Folder("camera",
                                                                                                                         True,
                                                                                                                         subfolders={"test_2": Folder("test_2", False), "test_3": Folder("test_3", True)})}),
                                             }
                                             ),

                             "behav": Folder("behav",
                                             self.cfg.use_behav,
                                             subfolders={"behav_camera":
                                                             Folder("camera",
                                                                    self.cfg.use_behav_camera
                                                                    )
                                                         }
                                             ),

                             "microscopy": Folder("microscopy",
                                                  self.cfg.use_microscopy,
                                                  subfolders={"test1": Folder("test_1", True)},
                                                  ),
                             }

    def make_config_file(self,
                         local_path: str,
                         remote_path: str,
                         remote_host_id: str,
                         remote_host_username: str,
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
        :param remote_path:                 path to project folder on remote machine
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
        config = {
            "local_path": local_path,
            "remote_path": remote_path,
            "remote_host_id": remote_host_id,  # TODO: this could be path (mounted) or server (SSH)
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

        with open(self._config_path, "w") as config_file:
            yaml.dump(config, config_file, sort_keys=False)

        self.cfg = self._attempt_load_configs(prompt_on_fail=False)
        self.set_attributes_after_config_load()
        print("Configuration file has been saved and options loaded into the project manager.")

    def _config_file_exists(self, prompt_on_fail : bool) -> bool:
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

            for path_key in ["local_path", "remote_path"]:
                config_dict[path_key] = Path(config_dict[path_key])

            config = SimpleNamespace(**config_dict)

        except:
            config = False

            if prompt_on_fail:
                print(f"Config file failed to load. Check file formatting at {self._config_path}. "
                      f"If cannot load, re-initialise configs with make_config_file()")

        return config

    # --------------------------------------------------------------------------------------------------------------------
    # Publicly Accessible Directory Makers
    # --------------------------------------------------------------------------------------------------------------------

    def make_mouse_folder(self, sub_names, ses_names=None, make_ses_tree=True):
        """"""
        sub_names = self._process_names(sub_names, "sub")

        if make_ses_tree:
            if ses_names is None:
                ses_names = [self.cfg.ses_prefix + "001"]  # TODO: default ses name
            else:
                ses_names = self._process_names(ses_names, "ses")
        else:
            ses_names = []

        self._make_directory_trees(sub_names, ses_names, make_ses_tree, process_names=False)

    def make_ses_folder(self, sub_names, ses_names, make_ses_tree=True):
        """"""
        self._make_directory_trees(sub_names, ses_names, make_ses_tree)

    def make_ses_tree(self, sub_names, ses_names):
        """"""
        self._make_directory_trees(sub_names, ses_names)

    def get_local_path(self):
        return self.cfg.local_path.as_posix()

    def get_appdir_path(self):
        return self._get_user_appdir_path().as_posix()

    # --------------------------------------------------------------------------------------------------------------------
    # Make Directory Trees
    # --------------------------------------------------------------------------------------------------------------------

    def _make_directory_trees(self, sub_names, ses_names, make_ses_tree=True, process_names=True):
        """"""
        sub_names = self._process_names(sub_names, "sub") if process_names else sub_names
        ses_names = self._process_names(ses_names, "ses") if process_names else ses_names

        for data_type_key, data_type_dir in self._ses_folders.items():

            if data_type_dir.used:
                self._make_dirs(self._join("local", data_type_dir.name))

                for sub in sub_names:

                    self._make_dirs(self._join("local", [data_type_dir.name, sub]))

                    for ses in ses_names:

                        self._make_dirs(self._join("local", [data_type_dir.name, sub, ses]))

                        if make_ses_tree:
                            self._make_ses_directory_tree(sub, ses, data_type_key)

    def _make_ses_directory_tree(self, sub, ses, top_level_key):  # TODO: use fully recursive structure by giving each folder class a function to make its own dir tree, much more extendable than this
        """
        Assumes sub, ses dir is already made
        """
        data_type_dir = self._ses_folders[top_level_key]

        if data_type_dir.used and data_type_dir.subfolders:
            self._recursive_make_subfolders(folder=data_type_dir,
                                            path_to_folder=[data_type_dir.name, sub, ses])

    def _recursive_make_subfolders(self, folder, path_to_folder):
        """
        assumes top level dir is already made and now just making subfolders
        """
        if folder.subfolders:
            for subfolder in folder.subfolders.values():
                if subfolder.used:
                    new_path_to_folder = path_to_folder + [subfolder.name]
                    self._make_dirs(self._join("local", new_path_to_folder))
                    self._recursive_make_subfolders(subfolder, new_path_to_folder)

    # --------------------------------------------------------------------------------------------------------------------
    # SSH
    # --------------------------------------------------------------------------------------------------------------------

    # 1) setup SSH key in windows, mac, linux
    # 2) ssh to remote server
    # 3) transfer file
    # 4) checks
    # TODO: need to setup different users for ssh key / test multiple users

    def write_public_key(self, filepath, key):  # TOOD: doc that paramiko can use private key only but use this method for ease for user use
        """"""

        self._write_public_key(os.path.join(app_path, self._username_ssh_key + ".pub"), key)  # TODO: convenience function for join, NOTE this is not used again just for user to see. Think if this will ever lead to divergence
        key = paramiko.RSAKey.from_private_key_file(os.path.join(self._get_user_appdir_path(), self._username_ssh_key))

        with open(filepath, "w") as public:
            public.write(key.get_base64())
        public.close()

    def _generate_and_write_ssh_key(self):
        """"""
        key = paramiko.RSAKey.generate(4096)
        app_path = self._get_user_appdir_path()

        key.write_private_key_file(os.path.join(app_path, self._username_ssh_key))  # self._join() is confusing

    def setup_ssh_key(self):  # TODO: write a function that checks private and public keys match
        """generate_ssh_key_and_copy_pub_to_remote_host"""
        # TODO: checks that these dont already exist.
        # TODO: setup method for local connection (not ssh - check host path)
        # TODO: logging
        self._generate_and_write_ssh_key()  # TODO: this does not freeze process

        password = getpass.getpass("Please enter password to setup SSH keys. You will not have to enter your password again.")

        key = paramiko.RSAKey.from_private_key_file(os.path.join(self._get_user_appdir_path(), self._username_ssh_key))

        self._add_public_key_to_remote_authorized_keys(password, key)

    def copy_file_to_server(self, filepath):
        """"""
        with paramiko.client.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # TODO https://stackoverflow.com/questions/10670217/paramiko-unknown-server#43093883, https://stackoverflow.com/questions/45892703/what-are-the-security-implications-of-paramiko-rejectpolicy-autoaddpolicy-warn
            client.connect(self.cfg.remote_host_id, username=self.username, key_filename=os.path.join(self._get_user_appdir_path(), self._username_ssh_key), look_for_keys=True)
            client.put(self._join("local", filepath), self._join("remote", filepath))  # TODO: see documentation and add test https://docs.paramiko.org/en/stable/api/sftp.html

            # TODO: support list of files
            # TODO: join_local, join_remote

            # stdin, stdout, stderr = client.exec_command('w')
            # print(stdout.read().decode())

    def _add_public_key_to_remote_authorized_keys(self, password, key):
        """ssh-copy-id but from any platform.Could be improved (i.e. use ssh-copy-id if possible / there is a python version for windows"""
        with paramiko.client.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # TODO https://stackoverflow.com/questions/10670217/paramiko-unknown-server#43093883, https://stackoverflow.com/questions/45892703/what-are-the-security-implications-of-paramiko-rejectpolicy-autoaddpolicy-warn
            client.connect(self.cfg.remote_host_id, username=self.username, password=password)

            client.exec_command("mkdir -p ~/.ssh/")  # not used ssh-copy-id as platform independent # TODO: check that formatting is the same as ssh-copy-id
            client.exec_command(f'echo "{key.get_name()} {key.get_base64()}" >> ~/.ssh/authorized_keys')  # double >> for concatenate
            client.exec_command("chmod 644 ~/.ssh/authorized_keys")
            client.exec_command("chmod 700 ~/.ssh/")

    # --------------------------------------------------------------------------------------------------------------------
    # Utils TODO: move
    # --------------------------------------------------------------------------------------------------------------------

    def _join(self, base, subfolders):
        """
        TODO: this function is kind of messy now
        """
        if base == "local":  # cannot use dict as paths not defined before cfg loaded
            base_dir = self.cfg.local_path
        elif base == "remote":
            base_dir = self.cfg.remote_path
        elif base == "appdir":
            base_dir = self._get_user_appdir_path()

        if type(subfolders) == str:
            subfolders = [subfolders]

        joined_path = "/".join([base_dir.as_posix()] + subfolders)  # don't use os.path.join, operating on list is easier

        return joined_path

    def _process_names(self, names, sub_or_ses):
        """"""
        if type(names) not in [str, list] or any([type(ele) != str for ele in names]):  # TODO: tidy up, decide whether to handle non-str types
            print("Ensure subject and session names are list of strings, or string")  # TODO: better error
            return False

        if type(names) == str:
            names = [names]

        if sub_or_ses == "sub":  # TODO: own function if required anywhere else
            prefix = self.cfg.sub_prefix
        elif sub_or_ses == "ses":
            prefix = self.cfg.ses_prefix

        prefixed_names = self._ensure_prefixes_on_list_of_names(names, prefix)

        if len(prefixed_names) != len(set(prefixed_names)):
            self._throw_error("Subject and session names but all be unqiue (i.e. there are no duplicates in list input)")

        return prefixed_names

    def _throw_error(self, message):
        """ TODO: custom exception classes? """
        raise BaseException(message)

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

    # --------------------------------------------------------------------------------------------------------------------
    # Handle Configs
    # --------------------------------------------------------------------------------------------------------------------

    def set_configs(self):
        pass

    def _check_configs(self):
        pass
