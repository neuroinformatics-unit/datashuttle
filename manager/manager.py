from types import SimpleNamespace
import os
import appdirs
import getpass

import paramiko.client

# Assumptions: the remote host is unix system
import yaml


class ProjectManager():  # TODO: typing!!!
    """

    """
    def __init__(self):

        self._config_path = self._join("appdir", "config.yaml")
        self.cfg = self._load_configs()                       # TODO: handle when there are no configs!

        self._username_ssh_key = self.cfg.username + "_ssh_key"

        self._ses_folders = {"ephys": Folder("ephys", None, self.cfg.use_ephys),  # TODO: decide whether to allow user to change names
                             "behav": Folder("behav",
                                             {"camera": Folder("camera", None, self.cfg.use_camera)},
                                             self.cfg.use_behav),
                             "microscopy": Folder("microscopy", None, self.cfg.use_microscopy),
                             }

    def make_config_file(self, username, remote_base, local_path, remote_path, sub_prefix="sub-", ses_prefix="ses-",
                         use_ephys=True, use_behav=True, use_camera=True, use_microscopy=True):
        """
        TODO: this does not currently consider file levels (e.g. behav > camera file structure).
              check if already exists, if so throw a overwrite warning
        """
        config = {
            "username": username,
            "remote_base": remote_base,
            "local_path": local_path,
            "remote_path": remote_path,
            "sub_prefix": sub_prefix,
            "ses_prefix": ses_prefix,
            "use_ephys": use_ephys,
            "use_behav": use_behav,
            "use_camera": use_camera,
            "use_microscopy": use_microscopy,
        }

        with open(self._config_path, "w") as config_file:
            yaml.dump(config, config_file, sort_keys=False)

    def _config_file_exists(self):
        return os.path.isfile(self._config_path)  # TODO: could make own var

    def _load_configs(self):
        """
        """
        with open(self._config_path, "r") as config_file:
            config_dict = yaml.full_load(config_file)

        config = SimpleNamespace(**config_dict)

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

    # --------------------------------------------------------------------------------------------------------------------
    # Make Directory Trees
    # --------------------------------------------------------------------------------------------------------------------

    def _make_directory_trees(self, sub_names, ses_names, make_ses_tree=True, process_names=True):
        """"""
        sub_names = self._process_names(sub_names, "sub") if process_names else sub_names
        ses_names = self._process_names(ses_names, "ses") if process_names else ses_names

        for sub in sub_names:

            self._make_dirs(self._join("local", sub))

            for ses in ses_names:

                self._make_dirs(self._join("local", sub, ses))

                if make_ses_tree:
                    self._make_ses_directory_tree(sub, ses)

    def _make_ses_directory_tree(self, sub, ses):  # TODO: use fully recursive structure by giving each folder class a function to make its own dir tree, much more extendable than this
        """
        Assumes sub, ses dir is already made
        """
        for data_dir in self._ses_folders.values():

            if data_dir.used:
                self._make_dirs(self._join("local", sub, [ses, data_dir.name]))

                if data_dir.subfolders:
                    for data_sub_dir in data_dir.subfolders.values():
                        if data_sub_dir.used:
                            self._make_dirs(self._join("local", sub, [ses, data_dir.name, data_sub_dir.name]))

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

    def show_appdir_path(self):
        print(self._get_user_appdir_path())  # TODO: not just print, depending on use (e.g. GUI)

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
            client.connect(self.cfg.remote_base, username=self.cfg.username, key_filename=os.path.join(self._get_user_appdir_path(), self._username_ssh_key), look_for_keys=True)
            client.put(self._join("local", filepath), self._join("remote", filepath))  # TODO: see documentation and add test https://docs.paramiko.org/en/stable/api/sftp.html

            # TODO: support list of files
            # TODO: join_local, join_remote

            # stdin, stdout, stderr = client.exec_command('w')
            # print(stdout.read().decode())

    def _add_public_key_to_remote_authorized_keys(self, password, key):
        """ssh-copy-id but from any platform.Could be improved (i.e. use ssh-copy-id if possible / there is a python version for windows"""
        with paramiko.client.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # TODO https://stackoverflow.com/questions/10670217/paramiko-unknown-server#43093883, https://stackoverflow.com/questions/45892703/what-are-the-security-implications-of-paramiko-rejectpolicy-autoaddpolicy-warn
            client.connect(self.cfg.remote_base, username=self.cfg.username, password=password)

            client.exec_command("mkdir -p ~/.ssh/")  # not used ssh-copy-id as platform independent # TODO: check that formatting is the same as ssh-copy-id
            client.exec_command(f'echo "{key.get_name()} {key.get_base64()}" >> ~/.ssh/authorized_keys')  # double >> for concatenate
            client.exec_command("chmod 644 ~/.ssh/authorized_keys")
            client.exec_command("chmod 700 ~/.ssh/")

    # --------------------------------------------------------------------------------------------------------------------
    # Utils TODO: move
    # --------------------------------------------------------------------------------------------------------------------

    def _join(self, base, sub, subfolders=None):
        """
        TODO: this function is kind of messy now
        """
        if base == "local":  # cannot use dict as paths not defined before cfg loaded
            base_dir = self.cfg.local_path
        elif base == "remote":
            base_dir = self.cfg.remote_path
        elif base == "appdir":
            base_dir = self._get_user_appdir_path()

        if subfolders is None:
            subfolders = []

        if type(subfolders) == str:
            subfolders = [subfolders]

        if type(sub) == str:
            sub = [sub]

        joined_path = "/".join([base_dir] + sub + subfolders)  # don't use os.path.join, operating on list is easier

        return joined_path

    def _process_names(self, names, sub_or_ses):                                        # TODO: add check for "sub" or "ses" ?
        """"""
        if type(names) not in [str, list] or any([type(ele) != str for ele in names]):  # TODO: tidy up, decide whether to handle non-str types
            print("Ensure subject and session names are list of strings, or string")    # TODO: better error
            return False

        if type(names) == str:
            names = [names]

        prefix = self.cfg.sub_prefix if sub_or_ses == "sub" else self.cfg.ses_prefix
        prefixed_names = self.ensure_prefixes_on_list_of_names(names, prefix)

        return prefixed_names

    @staticmethod
    def _get_user_appdir_path():
        """
        Iti s not possible to write to programfiles in windows from app without admin permissions
        However if admin permission given drag and drop dont work, and it is not good practice.
        Use appdirs module to get the AppData cross-platform and save / load all files form here .
        """
        base_path = appdirs.user_data_dir("ProjectManagerSWC")  # name need to match nsis?
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

    @staticmethod
    def ensure_prefixes_on_list_of_names(names, prefix):
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

    # --------------------------------------------------------------------------------------------------------------------
    # Folder Class
    # --------------------------------------------------------------------------------------------------------------------


class Folder():
    def __init__(self, name, subfolders, used):

        self.name = name
        self.subfolders = subfolders
        self.used = used
