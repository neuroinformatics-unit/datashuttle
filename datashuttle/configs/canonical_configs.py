"""Contains all information defining the required format of the Configs class.

This format is clearly specified because configs can be supplied
either from a file or dynamically, so careful validation is required.

If adding a new config key:
- First add the key to `get_canonical_configs()` and define its type in the same function
"""

from __future__ import annotations

import os
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs
from pathlib import Path

import typeguard

from datashuttle.utils import folders, utils
from datashuttle.utils.custom_exceptions import ConfigError


def get_canonical_configs() -> dict:
    """Return the only permitted types for DataShuttle config values."""
    canonical_configs = {
        "local_path": Union[str, Path],
        "central_path": Optional[Union[str, Path]],
        "connection_method": Optional[Literal["ssh", "local_filesystem"]],
        "central_host_id": Optional[str],
        "central_host_username": Optional[str],
    }

    return canonical_configs


def keys_str_on_file_but_path_in_class() -> list[str]:
    """Return a list of all config keys that are paths but stored as str in the file.

    These are converted to pathlib.Path objects when loaded.
    """
    return [
        "local_path",
        "central_path",
    ]


def get_default_ssh_port() -> int:
    """Get the default port used for SSH connections."""
    if "DS_SSH_PORT" in os.environ:
        return int(os.environ["DS_SSH_PORT"])
    else:
        return 22


# -----------------------------------------------------------------------------
# Check Configs
# -----------------------------------------------------------------------------


def check_dict_values_raise_on_fail(config_dict: Configs) -> None:
    """Perform checks on a DataShuttle Configs UserDict class.

    This should be run after any change to the configs
    (e.g. make_config_file, update_config_file, supply_config_file).

    This will raise an error if a condition is not met.

    Parameters
    ----------
    config_dict
        datashuttle config UserDict

    """
    canonical_dict = get_canonical_configs()

    for key in canonical_dict.keys():
        if key not in config_dict.keys():
            utils.log_and_raise_error(
                f"Loading Failed. The key '{key}' was not "
                f"found in the config. "
                f"Config file was not updated.",
                ConfigError,
            )

    for key in config_dict.keys():
        if key not in canonical_dict.keys():
            utils.log_and_raise_error(
                f"The config contains an invalid key: {key}. "
                f"Config file was not updated.",
                ConfigError,
            )

    check_config_types(config_dict)

    raise_on_bad_local_only_project_configs(config_dict)

    if list(config_dict.keys()) != list(canonical_dict.keys()):
        utils.log_and_raise_error(
            f"New config keys are in the wrong order. The"
            f" order should be: {canonical_dict.keys()}.",
            ConfigError,
        )

    raise_on_bad_path_syntax(
        config_dict["local_path"].as_posix(), "local_path"
    )

    if config_dict["central_path"] is not None:
        raise_on_bad_path_syntax(
            config_dict["central_path"].as_posix(), "central_path"
        )

    # Check SSH settings
    if config_dict["connection_method"] == "ssh" and (
        not config_dict["central_host_id"]
        or not config_dict["central_host_username"]
    ):
        utils.log_and_raise_error(
            "'central_host_id' and 'central_host_username' are "
            "required if 'connection_method' is 'ssh'.",
            ConfigError,
        )

    # Initialise the local project folder
    utils.print_message_to_user(
        f"Making project folder at: {config_dict['local_path']}"
    )
    try:
        folders.create_folders(config_dict["local_path"])
    except OSError:
        utils.log_and_raise_error(
            f"Could not make project folder at: {config_dict['local_path']}. "
            f"Config file not updated.",
            RuntimeError,
        )


def raise_on_bad_local_only_project_configs(config_dict: Configs) -> None:
    """Check that both or neither of `central_path` and `connection_method` are set.

    There is no circumstance where one is set and not the other. Either both are set
    ('full' project) or both are `None` ('local only' project).
    """
    params_are_none = local_only_configs_are_none(config_dict)

    if any(params_are_none):
        if not all(params_are_none):
            utils.log_and_raise_error(
                "Either both `central_path` and `connection_method` must be set, "
                "or must both be `None` (for local-project mode).",
                ConfigError,
            )


def local_only_configs_are_none(config_dict: Configs) -> list[bool]:
    """Check whether `central_path` and `connection_method` are both set to None."""
    return [
        config_dict[key] is None
        for key in ["central_path", "connection_method"]
    ]


def raise_on_bad_path_syntax(
    path_name: str,
    path_type: str,
) -> None:
    """Raise error if path contains unsupported patterns (e.g. ~, .)."""
    if path_name[0] == "~":
        utils.log_and_raise_error(
            f"{path_type} must contain the full folder path with no ~ syntax.",
            ConfigError,
        )

    # pathlib strips "./" so not checked.
    for bad_start in [".", "../"]:
        if path_name.startswith(bad_start):
            utils.log_and_raise_error(
                f"{path_type} must contain the full folder path "
                "with no dot syntax.",
                ConfigError,
            )


def check_config_types(config_dict: Configs) -> None:
    """Check the type of passed configs matches the canonical types."""
    required_types = get_canonical_configs()

    for key in config_dict.keys():
        expected_type = required_types[key]
        try:
            typeguard.check_type(config_dict[key], expected_type)
        except typeguard.TypeCheckError:
            utils.log_and_raise_error(
                f"The type of the value at '{key}' is incorrect, "
                f"it must be {expected_type}. "
                f"Config file was not updated.",
                ConfigError,
            )


# -----------------------------------------------------------------------------
# Persistent settings
# -----------------------------------------------------------------------------


def get_tui_config_defaults() -> Dict:
    """Return the default settings for the datatype checkboxes in the TUI.

    Two sets are maintained (one for  checkboxes on the create tab,
    the other for transfer tab) which have different defaults.
    By default, all broad datatype checkboxes are displayed,
    and narrow datatypes are hidden and turned off.
    """
    settings = {
        "tui": {
            "create_checkboxes_on": {},
            "transfer_checkboxes_on": {
                "all": {"on": True, "displayed": True},
                "all_datatype": {"on": False, "displayed": True},
                "all_non_datatype": {"on": False, "displayed": True},
            },
            "top_level_folder_select": {
                "create_tab": "rawdata",
                "toplevel_transfer": "rawdata",
                "custom_transfer": "rawdata",
            },
            "bypass_validation": False,
            "overwrite_existing_files": "never",
            "dry_run": False,
            "suggest_next_sub_ses_central": False,
        }
    }

    # Fill all datatype options
    for broad_key in get_broad_datatypes():
        settings["tui"]["create_checkboxes_on"][broad_key] = {  # type: ignore
            "on": True,
            "displayed": True,
        }
        settings["tui"]["transfer_checkboxes_on"][broad_key] = {  # type: ignore
            "on": False,
            "displayed": True,
        }

    for narrow_key in quick_get_narrow_datatypes():
        settings["tui"]["create_checkboxes_on"][narrow_key] = {  # type: ignore
            "on": False,
            "displayed": False,
        }
        settings["tui"]["transfer_checkboxes_on"][narrow_key] = {  # type: ignore
            "on": False,
            "displayed": False,
        }

    return settings


def get_name_templates_defaults() -> Dict:
    """Return the default values for name_templates."""
    return {"name_templates": {"on": False, "sub": None, "ses": None}}


def get_persistent_settings_defaults() -> Dict:
    """Return the default persistent settings maintained across sessions.

    Currently, these include settings for both the API and TUI, such as the
    working top level folder, TUI checkboxes, and name templates
    (i.e. regexp validation for sub and ses names).
    """
    settings = {}
    settings.update(get_tui_config_defaults())
    settings.update(get_name_templates_defaults())

    return settings


def get_datatypes() -> List[str]:
    """Return canonical list of datatype flags based on NeuroBlueprint.

    This must be kept up to date with the datatypes in the NeuroBlueprint specification.
    """
    return get_broad_datatypes() + quick_get_narrow_datatypes()


def get_broad_datatypes():
    """Return a list of broad datatypes."""
    return ["ephys", "behav", "funcimg", "anat"]


def get_narrow_datatypes():
    """Return the narrow datatype associated with each broad datatype.

    The mapping between broad and narrow datatypes is required for validation.
    """
    return {
        "behav": ["motion"],
        "ephys": ["ecephys", "icephys", "emg"],
        "funcimg": ["cscope", "f2pe", "fmri", "fusi"],
        "anat": [
            "2pe",
            "bf",
            "cars",
            "conf",
            "dic",
            "df",
            "fluo",
            "mpe",
            "nlo",
            "oct",
            "pc",
            "pli",
            "sem",
            "spim",
            "sr",
            "tem",
            "uct",
            "mri",
        ],
    }


def quick_get_narrow_datatypes():
    """Return a flat list of all narrow datatypes.

    This is a convenience wrapper around `get_narrow_datatypes()`.
    """
    all_narrow_datatypes = get_narrow_datatypes()
    top_level_keys = list(all_narrow_datatypes.keys())
    flat_narrow_datatypes = []

    for key in top_level_keys:
        flat_narrow_datatypes += all_narrow_datatypes[key]

    return flat_narrow_datatypes


def in_place_update_narrow_datatypes_if_required(user_settings: dict):
    """Update legacy settings with the new version format.

    In versions < v0.6.0, only 'broad' datatypes were implemented
    and available in the TUI. Since, 'narrow' datatypes are introduced
    and datatype tui can be set to be both on / off but also
    displayed / not displayed.

    This function converts the old format to the new format so that
    all broad datatype settings (on / off) are maintained in
    then new version. It does this by copying the full default
    parameters and overwriting them with the available user-set
    defaults. This is the best approach, as it maintains the
    order of the datatypes (otherwise, inserting non-existing
    datatypes into the user datatype dict results in the wrong order).

    """
    # Find out what is included in the loaded config file,
    # that determines its version

    has_narrow_datatypes = isinstance(
        user_settings["tui"]["create_checkboxes_on"]["behav"], dict
    )  # added 'narrow datatype' v0.6.0 with major refactor to dict

    all_narrow_datatypes = quick_get_narrow_datatypes()

    is_not_missing_any_narrow_datatypes = all(
        [
            dtype in user_settings["tui"]["create_checkboxes_on"]
            for dtype in all_narrow_datatypes
        ]
    )

    if is_not_missing_any_narrow_datatypes:
        assert all(
            [
                dtype in user_settings["tui"]["transfer_checkboxes_on"]
                for dtype in all_narrow_datatypes
            ]
        ), (
            "Somehow there are datatypes missing in `transfer_checkboxes_on` but not `create_checkboxes_on`"
        )

    if has_narrow_datatypes and is_not_missing_any_narrow_datatypes:
        return

    # Make a dictionary of the canonical configs to fill in with whatever
    # user data exists. This ensures the order of the keys is always the same.
    canonical_tui_configs = get_tui_config_defaults()

    new_checkbox_configs = {
        "create_checkboxes_on": (
            canonical_tui_configs["tui"]["create_checkboxes_on"]
        ),
        "transfer_checkboxes_on": (
            canonical_tui_configs["tui"]["transfer_checkboxes_on"]
        ),
    }

    # Copy the pre-existing settings unique to the transfer checkboxes
    for key in ["all", "all_datatype", "all_non_datatype"]:
        if has_narrow_datatypes:
            new_checkbox_configs["transfer_checkboxes_on"][key] = (
                user_settings["tui"]["transfer_checkboxes_on"][key]
            )
        else:
            new_checkbox_configs["transfer_checkboxes_on"][key]["on"] = (
                user_settings["tui"]["transfer_checkboxes_on"][key]
            )

    # Copy any datatype information that exists. Broad datatypes will all be there
    # but some narrow datatypes might be missing.
    for checkbox_type in ["create_checkboxes_on", "transfer_checkboxes_on"]:
        datatypes_that_user_has = list(
            user_settings["tui"][checkbox_type].keys()
        )

        for dtype in get_datatypes():
            if dtype in datatypes_that_user_has:
                if has_narrow_datatypes:
                    new_checkbox_configs[checkbox_type][dtype] = user_settings[
                        "tui"
                    ][checkbox_type][dtype]
                else:
                    # in versions < 0.6.0 the datatype settings was only a bool
                    # indicating whether the checkbox is on or not. New versions
                    # are a dictionary indicating if the checkbox is on ("on")
                    # and displayed ("displayed").
                    new_checkbox_configs[checkbox_type][dtype]["on"] = (
                        user_settings["tui"][checkbox_type][dtype]
                    )

        user_settings["tui"][checkbox_type] = new_checkbox_configs[
            checkbox_type
        ]
