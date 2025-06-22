from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union, cast

if TYPE_CHECKING:
    from collections.abc import ItemsView, KeysView, ValuesView

    from datashuttle.utils.custom_types import (
        OverwriteExistingFiles,
        TopLevelFolder,
    )

import copy
from collections import UserDict
from pathlib import Path

import yaml

from datashuttle.configs import (
    canonical_configs,
    canonical_folders,
    load_configs,
)
from datashuttle.utils import folders, utils


class Configs(UserDict):
    """Store and manage datashuttle configuration settings.

    The configs must match exactly the standard set
    in canonical_configs.py. If updating these configs,
    this should be done through changing canonical_configs.py
    """

    def __init__(
        self, project_name: str, file_path: Path, input_dict: Union[dict, None]
    ) -> None:
        """Initialize the Configs class with project name, file path, and config dictionary.

        Parameters
        ----------
        project_name
            Name of the datashuttle project.

        file_path
            full filepath to save the config .yaml file to.

        input_dict
            a dict of config key-value pairs to input dict.
            This must contain all canonical_config keys

        The input dict is checked that it conforms to the
        canonical standard by calling check_dict_values_raise_on_fail()

        project_name and all paths are set at runtime but not stored.

        """
        super(Configs, self).__init__(input_dict)

        self.project_name = project_name
        self.file_path = file_path

        self.logging_path: Path
        self.hostkeys_path: Path
        self.ssh_key_path: Path
        self.project_metadata_path: Path

    def setup_after_load(self) -> None:
        """Set up the config after loading it."""
        load_configs.convert_str_and_pathlib_paths(self, "str_to_path")
        self.ensure_local_and_central_path_end_in_project_name()
        self.check_dict_values_raise_on_fail()

    def ensure_local_and_central_path_end_in_project_name(self) -> None:
        """Ensure that the local and central path end in the name of the project."""
        for path_type in ["local_path", "central_path"]:
            if path_type == "central_path" and self[path_type] is None:
                continue

            # important to check for "." path name as these
            # disappear when paths are concatenated.
            canonical_configs.raise_on_bad_path_syntax(
                self[path_type].as_posix(), path_type
            )
            if self[path_type].name != self.project_name:
                self[path_type] = self[path_type] / self.project_name

    def check_dict_values_raise_on_fail(self) -> None:
        """Validate dictionary values against canonical config requirements.

        This will raise an error if the dictionary
        does not match the canonical keys and value types.
        """
        canonical_configs.check_dict_values_raise_on_fail(self)

    def keys(self) -> KeysView:
        """Return D.keys(), a set-like object providing a view on D's keys."""
        return self.data.keys()

    def items(self) -> ItemsView:
        """Return D.items(), a set-like object providing a view on D's items."""
        return self.data.items()

    def values(self) -> ValuesView:
        """Return D.values(), a set-like object providing a view on D's values."""
        return self.data.values()

    # -------------------------------------------------------------------------
    # Save / Load from file
    # -------------------------------------------------------------------------

    def dump_to_file(self) -> None:
        """Save the dictionary to .yaml file stored in self.file_path."""
        cfg_to_save = copy.deepcopy(self.data)
        load_configs.convert_str_and_pathlib_paths(cfg_to_save, "path_to_str")

        with open(self.file_path, "w") as config_file:
            yaml.dump(cfg_to_save, config_file, sort_keys=False)

    def load_from_file(self) -> None:
        """Load a config dict saved at .yaml file.

        Note this will not automatically check the configs are valid,
        this requires calling self.check_dict_values_raise_on_fail().
        """
        with open(self.file_path) as config_file:
            config_dict = yaml.full_load(config_file)

        load_configs.convert_str_and_pathlib_paths(config_dict, "str_to_path")

        self.data = config_dict

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

    def build_project_path(
        self,
        base: str,
        sub_folders: Union[str, list],
        top_level_folder: TopLevelFolder,
    ) -> Path:
        """Build a path by joining a base directory with subfolders.

        If the path already starts with the base directory,
        the base will not be joined again.

        Parameters
        ----------
        base
            "local", "central" or "datashuttle"

        sub_folders
            a list (or string for 1) of
            folder names to be joined into a path.
            If file included, must be last entry (with ext).

        top_level_folder
            either "rawdata" or "derivatives"

        Returns
        -------
        The full path to the `sub_folders` in the project.

        """
        if isinstance(sub_folders, list):
            sub_folders_str = "/".join(sub_folders)
        else:
            sub_folders_str = cast("str", sub_folders)

        sub_folders_path = Path(sub_folders_str)

        base_folder = self.get_base_folder(base, top_level_folder)

        if utils.path_starts_with_base_folder(base_folder, sub_folders_path):
            joined_path = sub_folders_path
        else:
            joined_path = base_folder / sub_folders_path

        return joined_path

    def get_base_folder(
        self,
        base: str,
        top_level_folder: TopLevelFolder,
    ) -> Path:
        """Return the full base path for the given top-level folder.

        Parameters
        ----------
        base
            Base path, "local", "central" or "datashuttle".

        top_level_folder
            Either "rawdata" or "derivatives".

        Returns
        -------
        Full path to the local or central project top level folder.

        """
        if base == "local":
            base_folder = self["local_path"] / top_level_folder
        elif base == "central":
            base_folder = self["central_path"] / top_level_folder

        return base_folder

    def get_rclone_config_name(
        self, connection_method: Optional[str] = None
    ) -> str:
        """Generate the rclone configuration name for the project.

        These configs are created by datashuttle but managed and stored by rclone.
        """
        if connection_method is None:
            connection_method = self["connection_method"]

        return f"central_{self.project_name}_{connection_method}"

    def make_rclone_transfer_options(
        self, overwrite_existing_files: OverwriteExistingFiles, dry_run: bool
    ) -> Dict:
        """Create a dictionary of rclone transfer options.

        Originally these arguments were collected from configs, but now
        they are passed via function arguments. The `show_transfer_progress`
        and `dry_run` options are fixed here.
        """
        allowed_overwrite = ["never", "always", "if_source_newer"]

        if overwrite_existing_files not in allowed_overwrite:
            utils.log_and_raise_error(
                f"`overwrite_existing_files` not "
                f"recognised, must be one of: "
                f"{allowed_overwrite}",
                ValueError,
            )

        return {
            "overwrite_existing_files": overwrite_existing_files,
            "show_transfer_progress": True,
            "transfer_verbosity": "vv",
            "dry_run": dry_run,
        }

    def init_paths(self) -> None:
        """Initialize paths used by datashuttle."""
        self.project_metadata_path = self["local_path"] / ".datashuttle"

        datashuttle_path, _ = canonical_folders.get_project_datashuttle_path(
            self.project_name
        )

        self.ssh_key_path = datashuttle_path / f"{self.project_name}_ssh_key"

        self.hostkeys_path = datashuttle_path / "hostkeys"

        self.logging_path = self.make_and_get_logging_path()

    def make_and_get_logging_path(
        self,
    ) -> Path:
        """Build and return the path where logs are stored.

        Create the directory if it does not already exist.
        """
        logging_path = self.project_metadata_path / "logs"
        folders.create_folders(logging_path)
        return logging_path

    def get_datatype_as_dict_items(
        self, datatype: Union[str, list]
    ) -> Union[ItemsView, zip]:
        """Return canonical datatypes as dictionary items.

        Returns all datatype items or a subset if specified.
        """
        if isinstance(datatype, str):
            datatype = [datatype]

        items: Union[ItemsView, zip]

        datatype_folders = canonical_folders.get_datatype_folders()

        if "all" in datatype:
            items = datatype_folders.items()
        else:
            items = zip(
                datatype,
                [datatype_folders[key] for key in datatype],
            )

        return items

    def is_local_project(self):
        """Return bool indicating if project is a local-only project.

        A project is 'local-only' if it has no `central_path` and `connection_method`.
        It can be used to make folders and validate, but not for transfer.
        """
        canonical_configs.raise_on_bad_local_only_project_configs(self)

        params_are_none = canonical_configs.local_only_configs_are_none(self)

        return all(params_are_none)
