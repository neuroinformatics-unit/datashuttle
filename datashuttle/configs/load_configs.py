import traceback
import warnings
from pathlib import Path
from typing import Optional, Union, overload

from datashuttle.utils import utils

from . import canonical_configs
from .configs import Configs

ConfigValueTypes = Union[Path, str, bool, None]

# -------------------------------------------------------------------
# Load Supplied Config
# -------------------------------------------------------------------


def make_config_file_attempt_load(config_path: Path) -> Optional[Configs]:
    """
    Try to load an existing config file, that was previously
    saved by Datashuttle. This should always work, unless
    not already initialised (prompt) or these have been
    changed manually. This function is very similar to
    supplied_configs_confirm_overwrite()
    but has different set of prompts and some different logic.
    """
    exists = config_path.is_file()

    if not exists:
        warnings.warn(
            "Configuration file has not been initialized. "
            "Use make_config_file() to setup before continuing."
        )
        return None

    new_cfg: Optional[Configs]

    new_cfg = Configs(config_path, None)

    try:
        new_cfg.load_from_file()

    except Exception:

        new_cfg = None

        utils.message_user(
            f"Config file failed to load. Check file "
            f"formatting at {config_path.as_posix()}. If "
            f"cannot load, re-initialise configs with "
            f"make_config_file()"
        )

    return new_cfg


def supplied_configs_confirm_overwrite(
    path_to_config: Path,
    warn: bool,
) -> Union[Configs, None]:
    """
    Try and load a supplied config file.
    """
    utils.log_and_raise_error_not_exists_or_not_yaml(path_to_config)

    if warn:
        input_ = utils.get_user_input(
            "This will overwrite the existing datashuttle config file."
            "If you wish to proceed, press y."
        )

        if input_ != "y":
            utils.log_and_message("y not pressed. Configs not updated.")
            return None

    try:

        new_cfg = Configs(path_to_config, None)
        new_cfg.load_from_file()

        new_cfg = handle_cli_or_supplied_config_bools(new_cfg)
        new_cfg.check_dict_values_and_inform_user()

        return new_cfg

    except BaseException:
        utils.log_and_message(traceback.format_exc())
        utils.log_and_message(
            "Could not load config file. Please check that "
            "the file is formatted correctly. "
        )
        return None


# -------------------------------------------------------------------
# Convert keys from string inputs
# -------------------------------------------------------------------


@overload
def handle_cli_or_supplied_config_bools(dict_: Configs) -> Configs:
    ...


@overload
def handle_cli_or_supplied_config_bools(dict_: dict) -> dict:
    ...


def handle_cli_or_supplied_config_bools(
    dict_: Union[Configs, dict]
) -> Union[Configs, dict]:
    """
    For supplied configs for CLI input args,
    in some instances bools will as string type.
    Handle this case here to cast to correct type.
    """
    for key in dict_.keys():
        dict_[key] = handle_bool(key, dict_[key])
    return dict_


def handle_bool(key: str, value: ConfigValueTypes) -> ConfigValueTypes:
    """
    In some instances (CLI call, supplied configs) the configs will
    be in string format rather than bool or None. Parse these
    here. This assumes bool are always passed as flags.
    """
    if key in canonical_configs.get_flags():

        if value in ["None", "none", None]:
            value = False

        if isinstance(value, str):
            if value not in ["True", "False", "true", "false"]:
                utils.log_and_raise_error(
                    f"Input value for {key} " f"must be True or False"
                )

            value = value in ["True", "true"]

    elif value in ["None", "none"]:
        value = None

    return value
