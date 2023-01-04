import copy
from collections import UserDict
from collections.abc import ItemsView, KeysView, ValuesView
from pathlib import Path
from typing import Any, Union

import yaml

from datashuttle.configs import canonical_configs
from datashuttle.utils import utils


class Configs(UserDict):
    """
    Class to hold the datashuttle configs.

    The configs must match exactly the standard set
    in canonical_configs.py. If updating these configs,
    this should be done through changing canonical_configs.py

    The input dict is checked that it conforms to the
    canonical standard by calling check_dict_values_raise_on_fail()

    Parameters
    ----------

    file_path :
        full filepath to save the config .yaml file to.

    input_dict :
        a dict of config key-value pairs to input dict.
        This must contain all canonical_config keys
    """

    def __init__(self, file_path: Path, input_dict: Union[dict, None]) -> None:
        super(Configs, self).__init__(input_dict)

        self.file_path = file_path
        self.keys_str_on_file_but_path_in_class = [
            "local_path",
            "remote_path",
        ]
        self.sub_prefix = "sub-"
        self.ses_prefix = "ses-"

    def setup_after_load(self) -> None:
        self.convert_str_and_pathlib_paths(self, "str_to_path")
        self.check_dict_values_raise_on_fail()

    def check_dict_values_raise_on_fail(self) -> None:
        """
        Check the values of the current dictionary are set
        correctly and will not cause downstream errors.

        This will raise an error if the dictionary
        does not match the canonical keys and value types.
        """
        canonical_configs.check_dict_values_raise_on_fail(self)

    def keys(self) -> KeysView:
        return self.data.keys()

    def items(self) -> ItemsView:
        return self.data.items()

    def values(self) -> ValuesView:
        return self.data.values()

    # --------------------------------------------------------------------
    # Save / Load from file
    # --------------------------------------------------------------------

    def dump_to_file(self) -> None:
        """
        Save the dictionary to .yaml file stored in self.file_path.
        """
        cfg_to_save = copy.deepcopy(self.data)
        self.convert_str_and_pathlib_paths(cfg_to_save, "path_to_str")

        with open(self.file_path, "w") as config_file:
            yaml.dump(cfg_to_save, config_file, sort_keys=False)

    def load_from_file(self) -> None:
        """
        Load a config dict saved at .yaml file. Note this will
        not automatically check the configs are valid, this
        requires calling self.check_dict_values_raise_on_fail()
        """
        with open(self.file_path, "r") as config_file:
            config_dict = yaml.full_load(config_file)

        self.convert_str_and_pathlib_paths(config_dict, "str_to_path")

        self.data = config_dict

    # --------------------------------------------------------------------
    # Update Configs
    # --------------------------------------------------------------------

    def update_an_entry(self, option_key: str, new_info: Any) -> None:
        """
        Convenience function to update individual entry of configuration
        file. The config file, and currently loaded self.cfg will be
        updated.

        In case an update is breaking, set to new value,
        test validity and revert if breaking change.

        Parameters
        ----------

        option_key : dictionary key of the option to change,
            see make_config_file()

        new_info : value to update the config too
        """
        if option_key not in self:
            utils.log_and_raise_error(f"'{option_key}' is not a valid config.")

        original_value = copy.deepcopy(self[option_key])

        if option_key in self.keys_str_on_file_but_path_in_class:
            new_info = Path(new_info)

        self[option_key] = new_info

        check_change = self.safe_check_current_dict_is_valid()

        if check_change["passed"]:
            self.dump_to_file()
            utils.log_and_message(
                f"{option_key} has been updated to {new_info}"
            )

            if option_key in ["connection_method", "remote_path"]:
                if self["connection_method"] == "ssh":
                    utils.log_and_message(
                        f"SSH will be used to connect to project directory at: {self['remote_path']}"
                    )
                elif self["connection_method"] == "local_filesystem":
                    utils.log_and_message(
                        f"Local filesystem will be used to connect to project "
                        f"directory at: {self['remote_path'].as_posix()}"
                    )
        else:
            self[option_key] = original_value
            utils.log_and_raise_error(
                f"\n{check_change['error']}\n{option_key} was not updated"
            )

    def safe_check_current_dict_is_valid(self) -> dict:
        """
        Check the dict, but do not raise error as
        we need to set the putatively changed key
        back to the state before change attempt.

        Propagate the error message so it can be
        shown later.
        """
        try:
            self.check_dict_values_raise_on_fail()
            return {"passed": True, "error": None}
        except BaseException as e:
            return {"passed": False, "error": str(e)}

    # --------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------

    def convert_str_and_pathlib_paths(
        self, config_dict: Union["Configs", dict], direction: str
    ) -> None:
        """
        Config paths are stored as str in the .yaml but used as Path
        in the module, so make the conversion here.

        Parameters
        ----------

        config_dict : DataShuttle.cfg dict of configs
        direction : "path_to_str" or "str_to_path"
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
                    utils.log_and_raise_error(
                        "Option must be 'path_to_str' or 'str_to_path'"
                    )
