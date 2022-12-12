import copy
import pathlib
import traceback
import warnings
from collections import UserDict
from pathlib import Path
from typing import Any, Union

import yaml

from datashuttle.utils_mod import canonical_configs, utils


class Configs(UserDict):
    """
    Class to hold the configs for DataShuttle operations.
    The configs must match exactly the standard set
    in utils.cannonical_configs. If updating these
    configs, This should be done here. This is setup to be
    make config settings explicit and provide easy checking
    for user-set config files.

    To generate a new config, pass the file_path to
    the config file and a dict of config key-value pairs
    to input dict. Next, check that the config dict
    conforms to the canonical standard by calling
    check_dict_values_and_inform_user()
    """

    def __init__(self, file_path, input_dict):
        super(Configs, self).__init__(input_dict)

        self.file_path = file_path
        self.keys_str_on_file_but_path_in_class = [
            "local_path",
            "remote_path_ssh",
            "remote_path_local",
        ]
        self.sub_prefix = "sub-"
        self.ses_prefix = "ses-"

    def setup_after_load(self):
        self.convert_str_and_pathlib_paths(self, "str_to_path")
        self.check_dict_values_and_inform_user()

    def check_dict_values_and_inform_user(self):
        """
        Check the values of the current dictionary are set
        correctly and will not cause downstream errors.
        """
        canonical_configs.check_dict_values_and_inform_user(self)

    # --------------------------------------------------------------------
    # Save / Load from file
    # --------------------------------------------------------------------

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

    # --------------------------------------------------------------------
    # Update Configs
    # --------------------------------------------------------------------

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
        if option_key not in self:
            utils.raise_error(f"'{option_key}' is not a valid config.")

        original_value = copy.deepcopy(self[option_key])

        if option_key in self.keys_str_on_file_but_path_in_class:
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
        except BaseException:
            traceback.format_exc()
            return False

    # --------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------

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

    def convert_str_and_pathlib_paths(self, config_dict: dict, direction: str):
        """
        Config paths are stored as str in the .yaml but used as Path
        in the module, so make the conversion here.

        :param config_dict:DataShuttle.cfg dict of configs
        :param direction: "path_to_str" or "str_to_path"
        """
        for path_key in self.keys_str_on_file_but_path_in_class:
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
