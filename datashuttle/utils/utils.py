from __future__ import annotations

import logging
import re
import traceback
from pathlib import Path
from typing import List, Literal, Tuple, Union, overload

from rich import print as rich_print

from . import folders

# --------------------------------------------------------------------------------------
# General Utils
# --------------------------------------------------------------------------------------


def log(message: str) -> None:
    """
    Log the message to the main initialised
    logger.
    """
    logger = logging.getLogger("datashuttle")
    logger.debug(message)


def log_and_message(message: str, use_rich: bool = False) -> None:
    """
    Log the message and send it to user.
    use_rich : is True, use rich's print() function
    """
    log(message)
    print_message_to_user(message, use_rich)


def log_and_raise_error(message: str) -> None:
    """
    Log the message before raising the same message as an error.
    """
    logger = logging.getLogger("datashuttle")
    logger.error(f"\n\n{' '.join(traceback.format_stack(limit=5))}")
    logger.error(message)
    raise_error(message)


def print_message_to_user(message: Union[str, list], use_rich=False) -> None:
    """
    Centralised way to send message.
    use_rich :  use rich's print() function.
    """
    if use_rich:
        rich_print(message)
    else:
        print(message)


def get_user_input(message: str) -> str:
    """
    Centralised way to get user input
    """
    input_ = input(message)
    return input_


def raise_error(message: str) -> None:
    """
    Temporary centralized way to raise and error
    """
    raise BaseException(message)


def get_datashuttle_path(project_name: str) -> Tuple[Path, Path]:
    """
    Get the datashuttle path where configuration files are stored.
    Also, return a temporary path in this for logging in
    some cases where local_path location is not clear.

    The datashuttle configuration path is stored in the user home
    folder.
    """
    base_path = Path.home() / ".datashuttle" / project_name
    temp_logs_path = base_path / "temp_logs"

    folders.make_folders(base_path)
    folders.make_folders(temp_logs_path)

    return base_path, temp_logs_path


def get_path_after_base_folder(base_folder: Path, path_: Path) -> Path:
    """
    Get path relative to the base folder, used in case user has
    passed entire path including local_path or remove_path.

    Parameters
    ----------

    base_folder : base folder that should be removed, usually
        local_path or remote_path

    path_ : path after base_folder that should be isolated
    """
    if path_already_stars_with_base_folder(base_folder, path_):
        return path_.relative_to(base_folder)
    return path_


def path_already_stars_with_base_folder(
    base_folder: Path, path_: Path
) -> bool:
    return path_.as_posix().startswith(base_folder.as_posix())


def log_and_raise_error_not_exists_or_not_yaml(path_to_config: Path) -> None:
    """
    Supplied config path must be a .yaml - use this function to check if the
    supplied config path is indeed .yaml.
    """
    if not path_to_config.exists():
        log_and_raise_error(f"No file found at: {path_to_config}.")

    if path_to_config.suffix not in [".yaml", ".yml"]:
        log_and_raise_error("The config file must be a YAML file.")


# TODO: test this method


@overload
def get_values_from_bids_formatted_name(
    all_names: List[str],
    key: str,
    return_as_int: Literal[True],
    sort: bool = False,
) -> List[int]:
    ...


@overload
def get_values_from_bids_formatted_name(
    all_names: List[str],
    key: str,
    return_as_int: Literal[False] = False,
    sort: bool = False,
) -> List[str]:
    ...


def get_values_from_bids_formatted_name(
    all_names: List[str],
    key: str,
    return_as_int: bool = False,
    sort: bool = False,
) -> Union[List[int], List[str]]:
    """
    Find the values associated with a key from a list of all
    BIDS-formatted file / folder names.
    """
    all_values = []
    for name in all_names:

        if key not in name:
            raise_error(f"They key {key} is not found in {name}")

        value = re.findall(f"{key}-(.*?)(?=_|$)", name)

        if len(value) > 1:
            raise_error(
                f"There is more than instance of {key} in {name}."
                f"BIDS names must contain only one instance of"
                f"each key."
            )

        if return_as_int:
            try:
                value_to_append = int(value[0])
            except ValueError:
                raise_error(f"Invalid character in subject number {name}")
        else:
            value_to_append = value[0]

        all_values.append(value_to_append)

    if sort:
        all_values = sorted(all_values)

    return all_values


def unpack_nested_list(main_list):
    """"""
    new_list = []
    for value in main_list:
        if isinstance(value, list):
            new_list += value
        else:
            new_list += [value]
    return new_list
