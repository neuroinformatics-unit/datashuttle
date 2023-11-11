from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional, Tuple, Union

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs

from itertools import chain

from ..configs import canonical_folders
from . import folders, utils

# -----------------------------------------------------------------------------
# Checking a standalone list of names
# -----------------------------------------------------------------------------

# 4) add tests for everything, ensure everything is tested.
# 3) Review what needs to be done
# 5) In a new PR, add the project wrapper.


def validate_list_of_names(
    names_list: List[str],
    prefix: Literal["sub", "ses"],
    error_or_warn: Literal["error", "warn"] = "error",
    check_duplicates=True,
    log=True,
) -> None:
    """
    Validate a list of subject or session names, ensuring
    they are formatted as per NeuroBlueprint.

    We cannot validate names with "@*@" tags in.
    """
    if len(names_list) == 0:
        return

    tests_to_run = [
        lambda: name_beings_with_bad_key(names_list, prefix),
        lambda: names_include_spaces(names_list, prefix),
        lambda: dashes_and_underscore_alternate_incorrectly(names_list),
        lambda: value_lengths_are_inconsistent(names_list, prefix),
    ]
    if check_duplicates:
        tests_to_run += [lambda: duplicated_prefix_values(names_list, prefix)]

    for test in tests_to_run:
        failed, message = test()
        if failed:
            raise_error_or_warn(message, error_or_warn, log)


# TODO: test
def name_beings_with_bad_key(
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> Tuple[bool, str]:  # TODO: test
    """ """
    bad_names = []
    for name in names_list:
        if name[:4] != f"{prefix}-":
            bad_names.append(name)

    if bad_names:
        message = (
            f"The names: {bad_names} "
            f"do not begin with the required prefix: {prefix}"
        )
        return True, message

    return False, ""


# TODO: test
def names_include_spaces(
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> Tuple[bool, str]:
    """ """
    bad_names = []
    for name in names_list:
        if " " in name:
            bad_names.append(name)

    if bad_names:
        return (
            True,
            f"The names {bad_names} include spaces, "
            f"which is not permitted.",
        )
    return False, ""


def dashes_and_underscore_alternate_incorrectly(
    names_list: List[str],
) -> Tuple[bool, str]:
    """ """
    bad_names = []
    for name in names_list:
        discrim = {"-": 1, "_": -1}

        dashes_underscores = [
            discrim[ele] for ele in name if ele in ["-", "_"]
        ]

        if dashes_underscores[0] != 1:
            bad_names.append(name)

        elif any([ele == 0 for ele in utils.diff(dashes_underscores)]):
            bad_names.append(name)

    if bad_names:
        message = (
            f"The names {bad_names} are not formatted correctly. Names"
            f"must consist of key-value pairs separated by underscores."
            f"e.g. 'sub-001_ses-01_date-20230516"
        )
        return True, message

    return False, ""


def value_lengths_are_inconsistent(
    names_list: List[str],
    prefix: Literal["sub", "ses"],
) -> Tuple[bool, str]:
    """
    Given a list of NeuroBlueprint-formatted subject or session
    names, determine if there are inconsistent value lengths for
    the sub or ses key.
    """
    prefix_values = utils.get_values_from_bids_formatted_name(
        names_list, prefix, return_as_int=False
    )

    value_len = [len(value) for value in prefix_values]

    inconsistent_value_len = value_len != [] and not all_identical(value_len)

    if inconsistent_value_len:
        message = (
            f"Inconsistent value lengths for the key {prefix} were "
            f"found. Ensure the number of digits for the {prefix} value "
            f"are the same and prefixed with leading zeros if required."
        )
        return True, message

    return False, ""


def duplicated_prefix_values(
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> Tuple[bool, str]:
    """
    Check a list of subject or session names for duplicate
    ids (e.g. not allowing ["sub-001", "sub-001_@DATE@"])
    """
    int_values = utils.get_values_from_bids_formatted_name(
        names_list, prefix, return_as_int=True
    )

    has_duplicate_ids = not all_unique(int_values)

    if has_duplicate_ids:
        message = (
            f"{prefix} names must all have unique integer ids"
            f" after the {prefix} prefix."
        )
        return True, message

    return False, ""


def raise_error_or_warn(
    message: str, error_or_warn: Literal["error", "warn"], log: bool
) -> None:
    """ """
    assert error_or_warn in ["error", "warn"], "Must be 'error' or 'warn'."

    # TODO: combine `log_and_raise_error` and `raise_error`
    if error_or_warn == "error":
        if log:
            utils.log_and_raise_error(message)
        else:
            utils.raise_error(message)
    else:
        utils.warn(message, log=log)


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------


def datatypes_are_invalid(
    datatype: Union[List[str], str], allow_all=False
) -> Tuple[bool, str]:
    """
    Check the passed datatype is valid (must be a key on
    self.ses_folders e.g. "behav", or "all")
    """
    datatype_folders = canonical_folders.get_datatype_folders()

    if isinstance(datatype, str):
        datatype = [datatype]

    valid_keys = list(datatype_folders.keys())
    if allow_all:
        valid_keys += ["all"]

    bad_datatypes = []
    for dt in datatype:
        if dt not in valid_keys:
            bad_datatypes.append(dt)

    if bad_datatypes:
        or_all = " or 'all'" if allow_all else ""
        message = (
            f"datatypes: '{bad_datatypes}' are not valid. Must be one of"
            f" {list(datatype_folders.keys())}{or_all}. "
            f"No folders were made."
        )
        return True, message

    return False, ""


# -----------------------------------------------------------------------------
# More integrated : Searching for Folders (then working on a list)
# -----------------------------------------------------------------------------


# TODO: this is getting very messy
def validate_project(
    cfg,
    local_only=False,
    error_or_warn: Literal["error", "warn"] = "error",
    log=True,
):
    """"""
    folder_names = folders.get_all_sub_and_ses_names(cfg, local_only)

    sub_names = folder_names["sub"]

    validate_list_of_names(
        sub_names,
        prefix="sub",
        error_or_warn=error_or_warn,
        log=log,
        check_duplicates=False,
    )

    for sub in sub_names:  # TODO: I think this includes many unnecessary loops
        failed, message = new_name_duplicates_existing(  # TODO: rename
            sub, sub_names, "sub"
        )
        if failed:
            raise_error_or_warn(message, error_or_warn, log)

    all_ses_names = list(chain(*folder_names["ses"].values()))

    validate_list_of_names(
        all_ses_names,
        "ses",
        check_duplicates=False,
        error_or_warn=error_or_warn,
        log=log,
    )
    # TODO: I think this includes many unnecessary loops
    for ses_names in folder_names["ses"].values():
        for ses in ses_names:
            failed, message = new_name_duplicates_existing(  # TODO: rename
                ses, ses_names, "ses"
            )
            if failed:
                raise_error_or_warn(message, error_or_warn, log)


def validate_names_against_project(
    cfg: Configs,
    sub_names: List[str],
    ses_names: Optional[List[str]] = None,
    local_only=False,
    error_or_warn: Literal["error", "warn"] = "error",
    log=True,
) -> None:
    """
    This does not support subject-specific checking, this needs to
    be handled a level up i.e. pass 1 sub, and it's sessions.
    It is presumed the sessions are for the subjects
    passed for the duplicate checks
    """
    folder_names = folders.get_all_sub_and_ses_names(cfg, local_only)

    if folder_names["sub"]:  # warn otherwise?
        validate_list_of_names(
            sub_names + folder_names["sub"],
            prefix="sub",
            check_duplicates=False,
        )

        for new_sub in sub_names:
            failed, message = new_name_duplicates_existing(
                new_sub, folder_names["sub"], "sub"
            )
            if failed:
                raise_error_or_warn(message, error_or_warn, log)

        if ses_names is not None:
            all_ses_names = list(set(chain(*folder_names["ses"].values())))

            validate_list_of_names(
                all_ses_names + ses_names, "ses", check_duplicates=False
            )

            # TODO: doc this, confusing.
            for new_sub in sub_names:
                if new_sub in folder_names["ses"]:
                    for new_ses in ses_names:
                        failed, message = new_name_duplicates_existing(
                            new_ses, folder_names["ses"][new_sub], "ses"
                        )
                        if failed:
                            raise_error_or_warn(message, error_or_warn, log)


def new_name_duplicates_existing(
    new_name: str, existing_names: List[str], prefix: Literal["sub", "ses"]
) -> Tuple[bool, str]:
    """
    Check that a subject or session does not already exist
    that shares a sub / ses id with the new_name.

    When creating new subject or session files, if the
    sub or ses id already exists, the full subject or session
    name should match exactly.

    For example, if "sub-001" exists, we can pass
    "sub-001" as a valid subject name (for example, when making sessions).
    However, if "sub-001_another-tag" exists, we should throw an
    error, because this shares the same subject id but refers to
    a different subject.
    """
    # Make a list of matches between `new_name` and any in `existing_names`
    for exist_name in existing_names:
        exist_name_id = utils.get_values_from_bids_formatted_name(
            [exist_name], prefix, return_as_int=True
        )[0]

        new_name_id = utils.get_values_from_bids_formatted_name(
            [new_name], prefix, return_as_int=True
        )[0]

        if exist_name_id == new_name_id:
            if new_name != exist_name:
                message = (
                    f"Cannot make folders. A {prefix} already exists with "
                    f"the same {prefix} id as {new_name}. "
                    f"The existing folder is {exist_name}."
                )
                return True, message

    return False, ""


# -----------------------------------------------------------------------------
# Utils (TODO: move to utils?)
# -----------------------------------------------------------------------------


def all_unique(list_: List) -> bool:
    return len(list_) == len(set(list_))


def all_identical(list_: List) -> bool:
    return len(set(list_)) == 1
