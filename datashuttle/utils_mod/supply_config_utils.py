import copy
from pathlib import Path
from typing import Optional, Union, get_args

from ..configs import Configs
from ..utils_mod import utils

# -----------------------------------------------------------------------------
# User Supplied Config
# -----------------------------------------------------------------------------
# This cannot be done in configs class because it requires instantiation of
# said configs class, which would be circular.


def try_to_load_user_config(
    supplied_cfg_path: Path,
    project_cfg: Configs,
    warn: bool,
) -> Optional[Configs]:
    """
    Check that the path points of a valid (yaml) file. Check
    for confirmation using input() as this will overwrite the
    existing configs. Try and load the config file, if successful,
    set the file_path to the used config_path, so it is dumped
    in the correct place
    """
    raise_error_not_exists_or_not_yaml(supplied_cfg_path)

    if warn:
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

    sorted_new_cfg = perform_checks_sort_raise_error_if_fails(
        project_cfg, new_cfg
    )

    if not sorted_new_cfg:
        return None

    return sorted_new_cfg


def perform_checks_sort_raise_error_if_fails(project_cfg, new_cfg):
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
    for key in project_cfg.keys():
        if key not in new_cfg.keys():
            utils.raise_error(
                f"Loading Failed. The key {key} was not "
                f"found in the supplied config. "
                f"Config file was not updated."
            )

    for key in new_cfg.keys():
        if key not in project_cfg.keys():
            utils.raise_error(
                f"The supplied config contains an invalid key: {key}. "
                f"Config file was not updated."
            )

    required_types = get_config_required_types()
    for key in project_cfg.keys():

        if not isinstance(new_cfg[key], get_args(required_types[key])):
            if key == "ssh_to_remote":
                breakpoint()
            utils.raise_error(
                f"The type of the value at {key} is incorrect, "
                f"it must be {type(project_cfg[key])}. "
                f"Config file was not updated."
            )

    sorted_new_cfg = copy.deepcopy(new_cfg)
    sorted_new_cfg.data = {key: new_cfg[key] for key in project_cfg.keys()}

    return sorted_new_cfg


def get_config_required_types():
    required_types = {
        "local_path": Union[str, Path, None],
        "ssh_to_remote": Union[bool, None],
        "remote_path_local": Union[str, Path, None],
        "remote_path_ssh": Union[str, Path, None],
        "remote_host_id": Union[str, None],
        "remote_host_username": Union[str, None],
        "use_ephys": Union[bool, None],
        "use_behav": Union[bool, None],
        "use_imaging": Union[bool, None],
        "use_histology": Union[bool, None],
    }
    return required_types


def raise_error_not_exists_or_not_yaml(supplied_cfg_path: Path):
    if not supplied_cfg_path.exists():
        utils.raise_error(
            f"No file found at supplied_cfg_path {supplied_cfg_path}"
        )

    if supplied_cfg_path.suffix not in [".yaml", ".yml"]:
        utils.raise_error("The config file must be a YAML file")
