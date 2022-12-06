import copy
import pathlib
import warnings
from collections import UserDict
from pathlib import Path
from typing import Any, Optional, Union

import yaml

from datashuttle.utils_mod import utils


class Configs(UserDict):
    """ """

    def __init__(self, file_path, input_dict):
        super(Configs, self).__init__(input_dict)

        self.file_path = file_path
        self.keys_str_on_file_but_path_in_class = [
            "local_path",
            "remote_path_ssh",
            "remote_path_local",
        ]

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
                "ssh to remote set but no remote_host_id or "
                "remote_host_username not provided."
            )

        if self["ssh_to_remote"] is False and (
            self["remote_host_id"] or self["remote_host_username"]
        ):
            warnings.warn(
                "SSH to remote is false, but remote_host_id or "
                "remote_host_username provided."
            )

        if type(self["sub_prefix"]) != str or type(self["ses_prefix"]) != str:
            utils.raise_error(
                "sub_prefix and ses_prefix must both be strings."
            )

        if type(self["ssh_to_remote"]) != bool:
            utils.raise_error("ssh_to_remote must be a boolean.")

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
        :param new_info: value to update the config to
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

    # -----------------------------------------------------------------------------
    # User Supplied Config
    # -----------------------------------------------------------------------------

    def try_to_load_user_config(
        self,
        supplied_cfg_path: Path,
    ) -> Optional[UserDict]:
        """
        Check that the path points of a valid (yaml) file. Check
        for confirmation using input() as this will overwrite the
        existing configs. Try and load the config file, if successful,
        set the file_path to the used config_path, so it is dumped
        in the correct place
        """
        self.raise_error_not_exists_or_not_yaml(supplied_cfg_path)

        input_ = utils.get_user_input(
            "This will overwrite the existing datashuttle config file."
            "If you wish to proceed, press y."
        )

        if input_ != "y":
            return None

        try:
            new_cfg = Configs(supplied_cfg_path, None)
            new_cfg.load_from_file()

        except BaseException:
            utils.message_user(
                "Could not load config file. Please check that "
                "the file is formatted correctly. "
                "Config file was not updated."
            )
            return None

        sorted_new_cfg = self.perform_checks_sort_raise_error_if_fails(new_cfg)

        if not sorted_new_cfg:
            return None

        return sorted_new_cfg

    def perform_checks_sort_raise_error_if_fails(self, new_cfg):
        """
        Check that all expected keys are in the new_cfg and
        no unexpected keys are in new_cfg. using loops rather
        than set() so informative error messages can be given.

        The format of the existing config (i.e. instance of
        this class on datashuttle) is assumed to be correct, and the
        new config is tested against this.

        Also check all types match between existing and new key.
        Finally, sort the dict_ so it is in the expected
        order (this shouldn't make a difference but is nice
        to keep consistent).
        """
        for key in self.keys():
            if key not in new_cfg.keys():
                utils.raise_error(
                    f"Loading Failed. The key {key} was not "
                    f"found in the supplied config. "
                    f"Config file was not updated."
                )

        for key in new_cfg.keys():
            if key not in self.keys():
                utils.raise_error(
                    f"The supplied config contains an invalid key: {key}. "
                    f"Config file was not updated."
                )

        for key in self.keys():
            if not isinstance(new_cfg[key], type(self[key])):
                utils.raise_error(
                    f"The type of the value at {key} is incorrect,"
                    f"it must be {type(self[key])}. "
                    f"Config file was not updated."
                )

        sorted_new_cfg = copy.deepcopy(new_cfg)
        sorted_new_cfg.data = {key: new_cfg[key] for key in self.keys()}

        return sorted_new_cfg

    def raise_error_not_exists_or_not_yaml(self, supplied_cfg_path: Path):

        if not supplied_cfg_path.exists():
            utils.raise_error(
                f"No file found at supplied_cfg_path {supplied_cfg_path}"
            )

        if supplied_cfg_path.suffix not in [".yaml", ".yml"]:
            utils.raise_error("The config file must be a YAML file")
