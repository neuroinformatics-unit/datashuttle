import copy
import pathlib
import warnings
from collections import UserDict
from pathlib import Path
from typing import Any, Union

import yaml

from datashuttle.utils_mod import utils


class Configs(UserDict):
    """ """

    def __init__(self, file_path, input_dict):
        super(Configs, self).__init__(input_dict)

        self.file_path = file_path

    def check_dict_values_and_inform_user(self):
        """
        Check the values of the current dictionary are set
        correctly and will not cause downstream errors.
        """

        # Check relevant remote_path is set
        if self["ssh_to_remote"]:
            if not self["remote_path_ssh"]:
                utils.raise_error(
                    "ssh to remote is on but remote_path_ssh "
                    "has not been set."
                )
        else:
            if not self["remote_path_local"]:
                utils.raise_error(
                    "ssh to remote is off but remote_path_local "
                    "has not been set."
                )

        # Check bad remote path format
        if self.get_remote_path().as_posix()[0] == "~":
            utils.raise_error(
                "remote_path must contain the full directory path "
                "with no ~ syntax"
            )

        # Check SSH settings
        if self["ssh_to_remote"] is True and (
            not self["remote_host_id"] or not self["remote_host_username"]
        ):
            utils.raise_error(
                "remote_host_id and remote_host_username are "
                "required if ssh_to_remote is True."
            )

        if self["ssh_to_remote"] is False and (
            self["remote_host_id"] or self["remote_host_username"]
        ):
            warnings.warn(
                "SSH to remote is false, but remote_host_id or "
                "remote_host_username provided."
            )

    def update_an_entry(self, option_key: str, new_info: Any):
        """
        Convenience function to update individual entry of configuration
        file. The config file, and currently loaded self.cfg will be
        updated.

        In case an update is breaking (e.g. use ssh_to_remote but
        no remote_host_id), set to new value, test validity and
        revert if breaking change.

        :param option_key: dictionary key of the option to change,
                           see make_config_file()
        :param new_info: value to update the config too
        """
        original_value = copy.deepcopy(self[option_key])

        if option_key in [
            "local_path",
            "remote_path_ssh",
            "remote_path_local",
        ]:
            new_info = Path(new_info)

        self[option_key] = new_info

        change_valid = self.safe_check_current_dict_is_valid()

        if change_valid:
            self.dump_to_file()
            utils.message_user(f"{option_key} has been updated to {new_info}")

            if option_key == "ssh_to_remote":
                if new_info:
                    utils.message_user(
                        f"SSH will be used to connect to project directory at:"
                        f" {self.get_remote_path(for_user=True)}"
                    )
                else:
                    utils.message_user(
                        f"Local filesystem will be used for project "
                        f"directory at: {self.get_remote_path(for_user=True)}"
                    )
        else:
            self[option_key] = original_value
            warnings.warn(f"{option_key} was not updated")
            self[option_key] = original_value

    def safe_check_current_dict_is_valid(self) -> bool:
        """ """
        try:
            self.check_dict_values_and_inform_user()
            return True

        except BaseException as e:
            warnings.warn(f"WARNING: {e}")
            return False

    def dump_to_file(self):
        """"""
        cfg_to_save = copy.deepcopy(self.data)
        self.convert_str_and_pathlib_paths(cfg_to_save, "path_to_str")

        with open(self.file_path, "w") as config_file:
            yaml.dump(cfg_to_save, config_file, sort_keys=False)

    def load_from_file(self):
        """"""
        with open(self.file_path, "r") as config_file:
            config_dict = yaml.full_load(config_file)

        self.convert_str_and_pathlib_paths(config_dict, "str_to_path")

        self.data = config_dict

    def setup_after_load(self):
        self.convert_str_and_pathlib_paths(self, "str_to_path")
        self.check_dict_values_and_inform_user()

    def get_remote_path(
        self, for_user: bool = False
    ) -> Union[pathlib.Path, str]:
        """
        Interpath function to get pathlib remote path
        based on using ssh or local filesystem.
        """
        remote_path = (
            self["remote_path_ssh"]
            if self["ssh_to_remote"]
            else self["remote_path_local"]
        )

        if for_user:
            return remote_path.as_posix()
        else:
            return remote_path

    @staticmethod
    def convert_str_and_pathlib_paths(config_dict: dict, direction: str):
        """
        Config paths are stored as str in the .yaml but used as Path
        in the module, so make the conversion here.

        :param config_dict:DataShuttle.cfg dict of configs
        :param direction: "path_to_str" or "str_to_path"
        """
        for path_key in ["local_path", "remote_path_local", "remote_path_ssh"]:
            value = config_dict[path_key]

            if value:
                if direction == "str_to_path":
                    config_dict[path_key] = Path(value)

                elif direction == "path_to_str":
                    if type(value) != str:
                        config_dict[path_key] = value.as_posix()

                else:
                    utils.raise_error(
                        "Option must be 'path_to_str' or 'str_to_path'"
                    )
