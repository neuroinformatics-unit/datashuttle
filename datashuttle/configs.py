import copy
import warnings
from collections import UserDict
from pathlib import Path
from typing import Union

import yaml

from datashuttle.utils_mod import utils


class Configs(UserDict):
    """ """

    def __init__(self, file_path, input_dict):
        super(Configs, self).__init__(input_dict)

        self.file_path = file_path

    def check_dict_values_and_inform_user(self):
        """ """
        if self["remote_path"][0] == "~":  # TODO: handle path or string
            utils.raise_error(
                "remote_path must contain the full directory path with no ~ syntax"
            )

        if self["ssh_to_remote"] is True and (
            not self["remote_host_id"] or not self["remote_host_username"]
        ):
            utils.raise_error(
                "ssh to remote set but no remote_host_id or remote_host_username not"
                " provided"
            )

        if self["ssh_to_remote"] is False and (
            self["remote_host_id"] or self["remote_host_username"]
        ):
            warnings.warn(
                "SSH to remote is false, but remote_host_id or remote_host_username"
                " provided"
            )

    def update_an_entry(self, option_key: str, new_info: Union[str, bool]):
        """
        Convenience function to update individual entry of configuration file.
        The config file, and currently loaded self.cfg will be updated.

        :param option_key: dictionary key of the option to change,
                           see make_config_file()
        :param new_info: value to update the config too
        """
        if option_key in ["local_path", "remote_path"]:
            new_info = Path(new_info)

        self[option_key] = new_info
        self.dump_to_file()

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
        self.check_dict_values_and_inform_user()
        self.convert_str_and_pathlib_paths(self, "str_to_path")

    @staticmethod
    def convert_str_and_pathlib_paths(config_dict: dict, direction: str):
        """
        Config paths are stored as str in the .yaml but used as Path
        in the module, so make the conversion here.

        :param config_dict:DataShuttle.cfg dict of configs
        :param direction: "path_to_str" or "str_to_path"
        """
        for path_key in ["local_path", "remote_path"]:
            value = config_dict[path_key]

            if direction == "str_to_path":
                config_dict[path_key] = Path(value)

            elif direction == "path_to_str":
                if type(value) != str:
                    config_dict[path_key] = value.as_posix()

            else:
                utils.raise_error(
                    "Option must be 'path_to_str' or 'str_to_path'"
                )
