import copy
from collections import UserDict
from collections.abc import ItemsView, KeysView, ValuesView
from pathlib import Path
from typing import Optional, Union, cast

import yaml

from datashuttle.configs import canonical_configs, canonical_folders
from datashuttle.utils import folders, utils


class Configs(UserDict):
    """
    Class to hold the datashuttle configs.

    The configs must match exactly the standard set
    in canonical_configs.py. If updating these configs,
    this should be done through changing canonical_configs.py

    The input dict is checked that it conforms to the
    canonical standard by calling check_dict_values_raise_on_fail()

    project_name and all paths are set at runtime but not stored.

    Parameters
    ----------

    file_path :
        full filepath to save the config .yaml file to.

    input_dict :
        a dict of config key-value pairs to input dict.
        This must contain all canonical_config keys
    """

    def __init__(
        self, project_name: str, file_path: Path, input_dict: Union[dict, None]
    ) -> None:
        super(Configs, self).__init__(input_dict)

        self.project_name = project_name
        self.file_path = file_path

        self.keys_str_on_file_but_path_in_class = [
            "local_path",
            "central_path",
        ]

        self.top_level_folder: str

        self.datatype_folders: dict
        self.logging_path: Path
        self.hostkeys_path: Path
        self.ssh_key_path: Path
        self.project_metadata_path: Path

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

    # -------------------------------------------------------------------------
    # Save / Load from file
    # -------------------------------------------------------------------------

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
                    if not isinstance(value, str):
                        config_dict[path_key] = value.as_posix()

                else:
                    utils.log_and_raise_error(
                        "Option must be 'path_to_str' or 'str_to_path'",
                        ValueError,
                    )

    def make_path(self, base: str, sub_folders: Union[str, list]) -> Path:
        """
        Function for joining relative path to base dir.
        If path already starts with base dir, the base
        dir will not be joined.

        Parameters
        ----------

        base: "local", "central" or "datashuttle"

        sub_folders: a list (or string for 1) of
            folder names to be joined into a path.
            If file included, must be last entry (with ext).
        """
        if isinstance(sub_folders, list):
            sub_folders_str = "/".join(sub_folders)
        else:
            sub_folders_str = cast(str, sub_folders)

        sub_folders_path = Path(sub_folders_str)

        base_folder = self.get_base_folder(base)

        if utils.path_already_stars_with_base_folder(
            base_folder, sub_folders_path
        ):
            joined_path = sub_folders_path
        else:
            joined_path = base_folder / sub_folders_path

        return joined_path

    def get_base_folder(self, base: str) -> Path:
        """
        Convenience function to return the full base path.

        Parameters
        ----------

        base : base path, "local", "central" or "datashuttle"

        """
        if base == "local":
            base_folder = self["local_path"] / self.top_level_folder
        elif base == "central":
            base_folder = self["central_path"] / self.top_level_folder
        elif base == "datashuttle":
            base_folder, _ = canonical_folders.get_project_datashuttle_path(
                self.project_name
            )
        return base_folder

    def get_rclone_config_name(
        self, connection_method: Optional[str] = None
    ) -> str:
        """
        Convenience function to get the rclone config
        name (these configs are created by datashuttle
        but managed and stored by rclone).
        """
        if connection_method is None:
            connection_method = self["connection_method"]

        return f"central_{self.project_name}_{connection_method}"

    def make_rclone_transfer_options(self, dry_run: bool):
        return {
            "overwrite_old_files": self["overwrite_old_files"],
            "transfer_verbosity": self["transfer_verbosity"],
            "show_transfer_progress": self["show_transfer_progress"],
            "dry_run": dry_run,
        }

    def init_paths(self):
        """"""
        self.project_metadata_path = self["local_path"] / ".datashuttle"

        self.ssh_key_path = self.make_path(
            "datashuttle", self.project_name + "_ssh_key"
        )

        self.hostkeys_path = self.make_path("datashuttle", "hostkeys")

        self.logging_path = self.make_and_get_logging_path()

    def make_and_get_logging_path(self) -> Path:
        """
        Currently logging is located in config path
        """
        logging_path = self.project_metadata_path / "logs"
        folders.make_folders(logging_path)
        return logging_path

    def init_datatype_folders(self):
        """"""
        self.datatype_folders = canonical_folders.get_datatype_folders(self)

    def get_datatype_items(
        self, datatype: Union[str, list]
    ) -> Union[ItemsView, zip]:
        """
        Get the .items() structure of the datatype, either all of
        them (stored in self.datatype_folders) or as a single item.
        """
        if isinstance(datatype, str):
            datatype = [datatype]

        items: Union[ItemsView, zip]

        if "all" in datatype:
            items = self.datatype_folders.items()
        else:
            items = zip(
                datatype,
                [self.datatype_folders[key] for key in datatype],
            )

        return items

    def items_from_datatype_input(
        self,
        local_or_central: str,
        datatype: Union[list, str],
        sub: str,
        ses: Optional[str] = None,
    ) -> Union[ItemsView, zip]:
        """
        Get the list of datatypes to transfer, either
        directly from user input, or by searching
        what is available if "all" is passed.

        Parameters
        ----------

        see _transfer_datatype() for parameters.
        """
        base_folder = self.get_base_folder(local_or_central)

        if datatype not in [
            "all",
            ["all"],
            "all_datatype",
            ["all_datatype"],
        ]:
            datatype_items = self.get_datatype_items(
                datatype,
            )
        else:
            datatype_items = folders.search_data_folders_sub_or_ses_level(
                self,
                base_folder,
                local_or_central,
                sub,
                ses,
            )

        return datatype_items
