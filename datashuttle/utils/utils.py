from __future__ import annotations

import re
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


def log_and_raise_error(message: str, exception: Any) -> None:
    """Log the message before raising the same message as an error."""
    if ds_logger.logging_is_active():
        logger = ds_logger.get_logger()
        logger.error(f"\n\n{' '.join(traceback.format_stack(limit=5))}")
        logger.error(message)
    raise_error(message, exception)


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


def raise_error(message: str, exception) -> None:
    """Centralized way to raise an error.

    The logger is closed to ensure it is not still running
    if a function call raises an exception in a python environment.
    """
    ds_logger.close_log_filehandler()
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
