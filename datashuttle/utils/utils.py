from __future__ import annotations

import getpass
import random
import re
import string
import sys
import traceback
import warnings
from typing import TYPE_CHECKING, Any, List, Literal, Union, overload

if TYPE_CHECKING:
    from pathlib import Path

from rich import print as rich_print

from datashuttle.utils import ds_logger
from datashuttle.utils.custom_exceptions import NeuroBlueprintError

# -----------------------------------------------------------------------------
# Centralised logging, errors, outputs, inputs
# -----------------------------------------------------------------------------


def log(message: str) -> None:
    """Log the message to the main initialised logger."""
    if ds_logger.logging_is_active():
        logger = ds_logger.get_logger()
        logger.debug(message)


def log_and_message(message: str, use_rich: bool = False) -> None:
    """Log the message and send it to user.

    Parameters
    ----------
    message
        Message to log and print to user.

    use_rich
        If True, use rich's print() function.

    """
    log(message)
    print_message_to_user(message, use_rich)


def log_and_raise_error(
    message: str, exception: Any, from_error: Exception | None = None
) -> None:
    """Log the message before raising the same message as an error."""
    if ds_logger.logging_is_active():
        logger = ds_logger.get_logger()
        logger.error(f"\n\n{' '.join(traceback.format_stack(limit=5))}")
        logger.error(message)
    raise_error(message, exception, from_error=from_error)


def warn(message: str, log: bool) -> None:
    """Send a warning.

    Parameters
    ----------
    message
        Message to warn.

    log
        If True, log at WARNING level.

    """
    if log and ds_logger.logging_is_active():
        logger = ds_logger.get_logger()
        logger.warning(message)
    warnings.warn(message)


def raise_error(
    message: str, exception, from_error: Exception | None = None
) -> None:
    """Centralized way to raise an error.

    The logger is closed to ensure it is not still running
    if a function call raises an exception in a python environment.
    """
    ds_logger.close_log_filehandler()

    if from_error:
        raise exception(message) from from_error
    else:
        raise exception(message)


def print_message_to_user(
    message: Union[str, list], use_rich: bool = False
) -> None:
    """Centralised way to send message.

    Parameters
    ----------
    message
        Message to print.

    use_rich
        If True, use rich's print() function.

    """
    if use_rich:
        rich_print(message)
    else:
        print(message)


def get_user_input(message: str) -> str:
    """Centralised way to get user input."""
    input_ = input(message)
    return input_


def get_connection_secret_from_user(
    connection_method_name: str,
    key_name_full: str,
    key_name_short: str,
    key_info: str | None = None,
    log_status: bool = True,
) -> str:
    """Get sensitive information input from the user via their terminal.

    This is a centralised function shared across connection methods.
    It checks whether the standard input (stdin) is connected to a
    terminal or not. If not, the user is displayed a warning and asked
    if they would like to continue.

    Parameters
    ----------
    connection_method_name
        A string identifying the connection method being used.

    key_name_full
        Full name of the connection secret being asked from the user.

    key_name_short
        Short name of the connection secret to avoid repeatedly writing the full name.

    key_info
        Extra info about the connection secret that needs to intimated to the user.

    log_status
        Log if `True`, logger must already be initialised.

    """
    if key_info:
        print_message_to_user(key_info)

    if not sys.stdin.isatty():
        proceed = input(
            f"\nWARNING!\nThe next step is to enter a {key_name_full}, but it is not possible\n"
            f"to hide your {key_name_short} while entering it in the current terminal.\n"
            f"This can occur if running the command in an IDE.\n\n"
            f"Press 'y' to proceed to {key_name_short} entry. "
            f"The characters will not be hidden!\n"
            f"Alternatively, run {connection_method_name} setup after starting Python in your "
            f"system terminal \nrather than through an IDE: "
        )
        if proceed != "y":
            print_message_to_user(
                f"Quitting {connection_method_name} setup as 'y' not pressed."
            )
            log_and_raise_error(
                f"{connection_method_name} setup aborted by user.",
                ConnectionAbortedError,
            )

        input_ = input(
            f"Please enter your {key_name_full}. Characters will not be hidden: "
        )

    else:
        input_ = getpass.getpass(f"Please enter your {key_name_full}: ")

    if log_status:
        log(f"{key_name_full} entered by user.")

    return input_


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------


def path_starts_with_base_folder(base_folder: Path, path_: Path) -> bool:
    """Return a bool indicating whether the path starts with the base folder path."""
    return path_.as_posix().startswith(base_folder.as_posix())


# -----------------------------------------------------------------------------
# BIDS names
# -----------------------------------------------------------------------------


@overload
def get_values_from_bids_formatted_name(
    all_names: List[str],
    key: str,
    return_as_int: Literal[True],
    sort: bool = False,
) -> List[int]: ...


@overload
def get_values_from_bids_formatted_name(
    all_names: List[str],
    key: str,
    return_as_int: Literal[False] = False,
    sort: bool = False,
) -> List[str]: ...


def get_values_from_bids_formatted_name(
    all_names: List[str],
    key: str,
    return_as_int: bool = False,
    sort: bool = False,
) -> Union[List[int], List[str]]:
    """Find the values associated with a key in a BIDS-style name.

    Parameters
    ----------
    all_names
        A list of names from which to find the value associated with the key.

    key
        Key from which to associate the values e.g. "sub")

    return_as_int
        If True and the value can be cast to int (e.g. `sub-001`), return as `int`.

    sort
        If True, results are sorted before being returned.

    Returns
    -------
    all_values
        The values of the corresponding `key` extracted from the name.

    Notes
    -----
    This function does not raise through datashuttle because we
    don't want to turn off logging, as some times these exceptions
    are caught and skipped.

    """
    all_values = []
    for name in all_names:
        if key not in name:
            raise NeuroBlueprintError(
                f"The key {key} is not found in {name}", KeyError
            )

        value = get_value_from_key_regexp(name, key)

        if len(value) > 1:
            raise NeuroBlueprintError(
                f"There is more than one instance of {key} in {name}. "
                f"NeuroBlueprint names must contain only one instance of "
                f"each key.",
            )

        if return_as_int:
            value_to_append = sub_or_ses_value_to_int(value[0])
        else:
            value_to_append = value[0]  # type: ignore

        all_values.append(value_to_append)

    if sort:
        all_values = sorted(all_values)

    return all_values


def sub_or_ses_value_to_int(value: str) -> int:
    """Return a subject or session value converted to an integer."""
    try:
        int_value = int(value)
    except ValueError:
        raise NeuroBlueprintError(
            f"Invalid character in subject or session value: {value}",
        )
    return int_value


def get_value_from_key_regexp(name: str, key: str) -> List[str]:
    """Return the value related to the key in a BIDS-style key-value pair name.

    e.g. sub-001_ses-312 would find 312 for key "ses".
    """
    return re.findall(f"{key}-(.*?)(?=_|$)", name)


# -----------------------------------------------------------------------------
# General Utils
# -----------------------------------------------------------------------------


def integers_are_consecutive(list_of_ints: List[int]) -> bool:
    """Return a bool indicating whether a list of integers is consecutive."""
    diff_between_ints = diff(list_of_ints)
    return all([diff == 1 for diff in diff_between_ints])


def diff(x: List) -> List:
    """Return differentiated list of numbers.

    Slow, only to avoid adding numpy as a dependency.
    """
    return [x[i + 1] - x[i] for i in range(len(x) - 1)]


def num_leading_zeros(name: str) -> int:
    """Return the number of leading zeros in a sub- or ses- id.

    e.g. sub-001 has 2 leading zeros.
    int() strips leading zeros.
    """
    if name[:4] in ["sub-", "ses-"]:
        name = name[4:]

    return len(name) - len(str(int(name)))


def all_unique(list_: List) -> bool:
    """Return bool indicating whether all values in a list are different."""
    return len(list_) == len(set(list_))


def all_identical(list_: List) -> bool:
    """Return bool indicating whether all values in a list are identical."""
    return len(set(list_)) == 1


def get_random_string(num_chars: int = 15) -> str:
    """Return a random string of alphanumeric characters."""
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choices(characters, k=num_chars))

    return random_string
