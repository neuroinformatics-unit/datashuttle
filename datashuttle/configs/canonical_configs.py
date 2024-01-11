"""
This module contains all information for the required
format of the configs class. This is clearly defined
as configs can be provided from file or input dynamically
and so careful checks must be done.

If adding a new config, first add the key to
get_canonical_config_dict() and type to
get_canonical_config_required_types()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs
from pathlib import Path
from typing import Literal, Union, get_args, get_origin

from datashuttle.utils import utils
from datashuttle.utils.custom_exceptions import ConfigError


# TODO: this can be merged with get_canonical_config_required_types()
def get_canonical_config_dict() -> dict:
    """
    Canonical list of required keys
    in the datashuttle configs
    """
    config_dict = {
        "local_path": None,
        "central_path": None,
        "connection_method": None,
        "central_host_id": None,
        "central_host_username": None,
        "overwrite_old_files": None,
        "transfer_verbosity": None,
        "show_transfer_progress": None,
    }

    return config_dict


def get_datatypes() -> List[str]:
    """
    Canonical list of datatype flags based on
    NeuroBlueprint.
    """
    return ["ephys", "behav", "funcimg", "anat"]


def get_flags() -> List[str]:
    """
    Return all configs that are bool flags. This is used in
    testing and type checking config inputs.
    """
    return [
        "overwrite_old_files",
        "show_transfer_progress",
    ]


def get_canonical_config_required_types() -> dict:
    """
    The only permitted types for DataShuttle
    config values.
    """
    required_types = {
        "local_path": Union[str, Path],
        "central_path": Union[str, Path],
        "connection_method": Literal["ssh", "local_filesystem"],
        "central_host_id": Union[str, None],
        "central_host_username": Union[str, None],
        "overwrite_old_files": bool,
        "transfer_verbosity": Literal["v", "vv"],
        "show_transfer_progress": bool,
    }

    assert (
        required_types.keys() == get_canonical_config_dict().keys()
    ), "update get_canonical_config_required_types with required types."

    return required_types


# -------------------------------------------------------------------
# Check Configs
# -------------------------------------------------------------------


def check_dict_values_raise_on_fail(config_dict: Configs) -> None:
    """
    Central function for performing checks on a
    DataShuttle Configs UserDict class. This should
    be run after any change to the configs (e.g.
    make_config_file, update_config_file(), supply_config_file).

    This will raise assert if condition is not met.

    Parameters
    ----------

    config_dict : datashuttle config UserDict
    """
    canonical_dict = get_canonical_config_dict()

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

    if list(config_dict.keys()) != list(canonical_dict.keys()):
        utils.log_and_raise_error(
            f"New config keys are in the wrong order. The"
            f" order should be: {canonical_dict.keys()}.",
            ConfigError,
        )

    if config_dict["connection_method"] not in ["ssh", "local_filesystem"]:
        utils.log_and_raise_error(
            "'connection method' must be 'ssh' or 'local_filesystem'.",
            ConfigError,
        )

    for path_type in ["local_path", "central_path"]:
        path_name = config_dict[path_type].as_posix()
        if path_name[0] == "~":
            utils.log_and_raise_error(
                f"{path_type} must contain the full folder path "
                "with no ~ syntax.",
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

        project_name = config_dict.project_name
        if config_dict[path_type].stem != project_name:
            utils.log_and_raise_error(
                f"The {path_type} does not end in the project name: {project_name}. \n"
                f"The last folder in the passed {path_type} should be {project_name}.\n"
                f"The passed path was {config_dict[path_type]}",
                ConfigError,
            )

    check_folder_above_project_name_exists(config_dict)

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

    # Transfer settings
    if config_dict["transfer_verbosity"] not in ["v", "vv"]:
        utils.log_and_raise_error(
            "'transfer_verbosity' must be either 'v' or 'vv'. Config not updated.",
            ConfigError,
        )

    # Initialise the local project folder
    try:
        utils.print_message_to_user(
            f"Making project folder at: {config_dict['local_path']}"
        )
        # TODO: cannot use folders.makefoldesr due to circular import
        config_dict["local_path"].mkdir(parents=True, exist_ok=True)

    except OSError:
        utils.log_and_raise_error(
            f"Could not make project folder at: {config_dict['local_path']}."
            f" Config file not updated.",
            RuntimeError,
        )


def check_folder_above_project_name_exists(config_dict: Configs):
    """
    Throw an error if the path above the project root does not exist.
    This validation is necessary (rather than simply creating the passed folders)
    is to ensure the `local_path` or `central_path` are not accidentally set to a wrong
    location.

    If the `connection_method` is "ssh" is it not possible to check the central
    path at this stage.
    """

    def base_error_message(path_name):
        return (
            f"The {path_name}: {config_dict[path_name].parent} that the project folder "
            f"will reside in does not yet exist. Please ensure the path shown in this "
            f"message exists before continuing."
        )

    if not (config_dict["local_path"].parent.is_dir()):
        if config_dict["connection_method"] == "ssh":
            extra_warning = (
                "Also make sure the central_path`, is correct, as datashuttle "
                "cannot check it via SSH at this stage."
            )
        else:
            extra_warning = ""

        utils.log_and_raise_error(
            f"{base_error_message('local_path')} {extra_warning}",
            FileNotFoundError,
        )

    if (
        config_dict["connection_method"] == "local_filesystem"
        and not config_dict["central_path"].parent.is_dir()
    ):
        utils.log_and_raise_error(
            base_error_message("central_path"), FileNotFoundError
        )


def check_config_types(config_dict: Configs) -> None:
    """
    Check the type of passed configs matched canonical types.
    This is a sub-function of check_dict_values_raise_on_fail()

    Notes
    ------

    This is a little awkward as testing types against
    Union is not neat. To do this you can use
    isinstance(type, get_args(Union[types])).
    But get_args() will be empty if there is only
    one type in union. So we need to test the
    two cases explicitly.
    """
    required_types = get_canonical_config_required_types()
    fail = False

    for key in config_dict.keys():
        expected_type = required_types[key]

        if get_origin(expected_type) is Literal:
            if config_dict[key] not in get_args(expected_type):
                utils.log_and_raise_error(
                    f"'{config_dict[key]}' not in {get_args(expected_type)}",
                    ConfigError,
                )

        elif len(get_args(required_types[key])) == 0:
            if not isinstance(config_dict[key], expected_type):
                fail = True
        else:
            if not isinstance(config_dict[key], get_args(expected_type)):
                fail = True

        if fail:
            utils.log_and_raise_error(
                f"The type of the value at '{key}' is incorrect, "
                f"it must be {expected_type}. "
                f"Config file was not updated.",
                ConfigError,
            )
