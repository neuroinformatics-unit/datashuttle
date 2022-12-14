import traceback
from pathlib import Path
from typing import Union, overload

from datashuttle.utils import utils

from .configs import Configs

ConfigValueTypes = Union[Path, str, bool, None]

# -------------------------------------------------------------------
# Load Supplied Config
# -------------------------------------------------------------------


def get_confirmation_raise_on_fail(
    path_to_config: Path,
    warn: bool,
) -> Union[Configs, None]:
    """ """
    utils.raise_error_not_exists_or_not_yaml(path_to_config)

    if warn:
        input_ = utils.get_user_input(
            "This will overwrite the existing datashuttle config file."
            "If you wish to proceed, press y."
        )

        if input_ != "y":
            return None

    try:

        new_cfg = Configs(path_to_config, None)
        new_cfg.load_from_file()

        new_cfg = handle_cli_or_supplied_config_bools(new_cfg)
        new_cfg.check_dict_values_and_inform_user()

        return new_cfg

    except BaseException:
        utils.message_user(traceback.format_exc())
        utils.raise_error(
            "Could not load config file. Please check that "
            "the file is formatted correctly. "
            "Config file was not updated."
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
    """ """
    if key in [
        "use_ephys",
        "use_behav",
        "use_funcimg",
        "use_histology",
    ]:

        if value in ["None", "none", None]:
            value = False

        if isinstance(value, str):
            if value not in ["True", "False", "true", "false"]:
                utils.raise_error(
                    f"Input value for {key} " f"must be True or False"
                )

            value = value in ["True", "true"]

    elif value in ["None", "none"]:
        value = None

    return value
