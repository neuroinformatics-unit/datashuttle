from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union

if TYPE_CHECKING:
    from datashuttle import DataShuttle
    from datashuttle.configs.config_class import Configs

import warnings
from itertools import compress
from pathlib import Path

from ..configs import canonical_folders
from . import folders, utils

# -----------------------------------------------------------------------------
# Checking a standalone list of names
# -----------------------------------------------------------------------------


def validate_list_of_names(
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> None:
    """
    Validate a list of subject or session names, ensuring
    they are formatted as per NeuroBlueprint.

    We cannot validate names with "@*@" tags in.
    """
    if len(names_list) == 0:
        return

    check_all_names_begin_with_prefix(names_list, prefix)

    check_list_of_names_for_spaces(names_list, prefix)

    check_dashes_and_underscore_alternate_correctly(names_list)

    check_names_for_inconsistent_value_lengths(
        names_list, prefix, raise_error=True
    )

    check_names_for_duplicate_ids(names_list, prefix)


def check_all_names_begin_with_prefix(
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> None:  # TODO: test
    """ """
    begin_with_prefix = all([name[:4] == f"{prefix}-" for name in names_list])

    if not begin_with_prefix:
        utils.log_and_raise_error(
            f"Not all names in the list: {names_list} "
            f"begin with the required prefix: {prefix}"
        )


def check_list_of_names_for_spaces(  # TODO: test
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> None:
    """ """
    if any([" " in ele for ele in names_list]):
        utils.log_and_raise_error(f"{prefix} names cannot include spaces.")


def check_dashes_and_underscore_alternate_correctly(
    names_list: List[str],
) -> None:
    """ """
    for name in names_list:
        discrim = {"-": 1, "_": -1}
        dashes_underscores = [
            discrim[ele] for ele in name if ele in ["-", "_"]
        ]

        if dashes_underscores[0] != 1:
            utils.log_and_raise_error(
                "The first delimiter of 'sub' or 'ses' "
                "must be dash not underscore e.g. sub-001."
            )

        # TODO: this handles the suffix case, but suffixes are not
        # allowed at sub / ses level. Shall we allow them anyways?
        if len(dashes_underscores) % 2 != 0:
            dashes_underscores.pop(-1)

        if any([ele == 0 for ele in utils.diff(dashes_underscores)]):
            utils.log_and_raise_error(
                "Subject and session names must contain alternating dashes "
                "and underscores (used for separating key-value pairs)."
            )


def check_names_for_inconsistent_value_lengths(
    names_list: List[str],
    prefix: Literal["sub", "ses"],
    raise_error=False,
) -> bool:
    """
    Given a list of NeuroBlueprint-formatted subject or session
    names, determine if there are inconsistent value lengths for
    the sub or ses key.
    """
    prefix_values = utils.get_values_from_bids_formatted_name(
        names_list, prefix, return_as_int=False
    )

    value_len = [len(value) for value in prefix_values]

    if value_len != [] and not all_identical(value_len):
        inconsistent_lengths = True
    else:
        inconsistent_lengths = False

    if raise_error:
        utils.log_and_raise_error(
            f"Inconsistent value lengths for the key {prefix} were found. "
            f"Ensure the number of digits for the {prefix} value are the same "
            f"and prefixed with leading zeros if required."
        )

    return inconsistent_lengths


def check_names_for_duplicate_ids(
    names_list: List[str], prefix: Literal["sub", "ses"]
) -> None:
    """
    Check a list of subject or session names for duplicate
    ids (e.g. not allowing ["sub-001", "sub-001_@DATE@"])
    """
    int_values = utils.get_values_from_bids_formatted_name(
        names_list, prefix, return_as_int=True
    )
    if not all_unique(int_values):
        utils.log_and_raise_error(
            f"{prefix} names must all have unique integer ids"
            f" after the {prefix} prefix."
        )


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------


def check_datatype_is_valid(
    datatype: Union[List[str], str], error_on_fail: bool, allow_all=False
) -> bool:
    """
    Check the passed datatype is valid (must
    be a key on self.ses_folders e.g. "behav", or "all")
    """
    datatype_folders = canonical_folders.get_datatype_folders()

    if isinstance(datatype, str):
        datatype = [datatype]

    valid_keys = list(datatype_folders.keys())
    if allow_all:
        valid_keys += ["all"]

    is_valid = all([type in valid_keys for type in datatype])

    if error_on_fail and not is_valid:
        utils.log_and_raise_error(
            f"datatype: '{datatype}' "
            f"is not valid. Must be one of"
            f" {list(datatype_folders.keys())}. or 'all'"
            f" No folders were made."
        )

    return is_valid


# -----------------------------------------------------------------------------
# More integrated : Searching for Folders (then working on a list)
# -----------------------------------------------------------------------------


def all_unique(list_: List) -> bool:
    return len(list_) == len(set(list_))


def all_identical(list_: List) -> bool:
    return len(set(list_)) == 1


def check_no_duplicate_sub_ses_key_values(
    project: DataShuttle,
    base_folder: Path,
    new_sub_names: List[str],
    new_ses_names: Optional[List[str]] = None,
) -> None:
    """
    Given a list of subject and optional session names,
    check whether these already exist in the local project
    folder.

    This uses search_sub_or_ses_level() to search the local
    folder and then checks for the putative new subject
    or session names to determine any matches.

    Parameters
    ----------

    project : initialised datashuttle project

    base_folder : local_path to search

    new_sub_names : list of subject names that are being
     checked for duplicates

    new_ses_names : list of session names that are being
     checked for duplicates
    """
    if new_ses_names == []:
        new_ses_names = None

    for new_sub in new_sub_names:
        existing_names = folders.search_sub_or_ses_level(
            project.cfg, base_folder, "local", search_str="*sub-*"
        )[0]

        check_new_subject_does_not_duplicate_existing(
            new_sub, existing_names, "sub"
        )

    if new_ses_names is not None:
        for sub in new_sub_names:
            existing_names = folders.search_sub_or_ses_level(
                project.cfg, base_folder, "local", sub, search_str="*ses-*"
            )[0]

            for new_ses in new_ses_names:
                check_new_subject_does_not_duplicate_existing(
                    new_ses, existing_names, "ses"
                )


def check_new_subject_does_not_duplicate_existing(
    new_name: str, existing_names: List[str], prefix: Literal["sub", "ses"]
) -> None:
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
    # For every existing subject / session name,
    # check whether the id matches the new name. If it
    # does, add the full name to `matched_existing_names`.
    matched_existing_names = []
    for exist_name in existing_names:
        exist_name_id = utils.get_values_from_bids_formatted_name(
            [exist_name], prefix, return_as_int=True
        )[0]
        new_name_id = utils.get_values_from_bids_formatted_name(
            [new_name], prefix, return_as_int=True
        )[0]

        if exist_name_id == new_name_id:
            matched_existing_names.append(exist_name)

    # We expect either zero matches (subject or session with matching id
    # does not exist. We can pass this case, as file will be made).
    # If more than 1 duplicates already exist, raise.
    # If exactly one exists, check it matches the new name exactly. Otherwise,
    # it is a duplicate.
    if len(matched_existing_names) > 1:
        utils.log_and_raise_error(
            f"Cannot make folders. Multiple {prefix} ids "
            f"exist: {matched_existing_names}. This should"
            f"never happen. Check the {prefix} ids and ensure unique {prefix} "
            f"ids (e.g. sub-001) appear only once."
        )

    if len(matched_existing_names) == 1:
        if new_name != matched_existing_names[0]:
            utils.log_and_raise_error(
                f"Cannot make folders. A {prefix} already exists "
                f"with the same {prefix} id as {new_name}. "
                f"The existing folder is {matched_existing_names[0]}."
            )


# Sub or ses value length checks
# -----------------------------------------------------------------------------


def warn_on_inconsistent_sub_or_ses_value_lengths(
    cfg: Configs,
):
    """
    Determine if there are inconsistent value lengths across the
    project (i.e. this local machine and the central machine.
    For example, there are inconsistent leading zeros in the list
    ["sub-001", "sub-02"], but not ["sub-001", "sub-002"]).

    If the number of sub or ses value lengths are not consistent (across local
    and remote repositories), then throw a warning. It is allowed for subjects
    and session folder names to have inconsistent leading zeros. But, within
    subject or session names, the value lengths must be consistent
    across local and central projects.
    """
    try:
        is_inconsistent = project_has_inconsistent_sub_or_ses_value_lengths(
            cfg
        )
    except:
        warnings.warn(
            "Could not search local and remote repositories. "
            "sub or ses key value length checks not performed."
        )
        return

    failing_cases = list(
        compress(
            ["sub", "ses"], [is_inconsistent["sub"], is_inconsistent["ses"]]
        )
    )

    if any(failing_cases):
        for fail_name in failing_cases:
            message = (
                f"Inconsistent value lengths for "
                f"the {fail_name} key in the project found. It is crucial "
                f"these are made consistent as soon as possible to "
                f"avoid unexpected behaviour of DataShuttle during "
                f"data transfer."
            )
            warnings.warn(message)

    else:
        utils.print_message_to_user(
            "No cases of inconsistent value lengths for subject or session"
            "found across this local machine and the central machine."
        )


def project_has_inconsistent_sub_or_ses_value_lengths(
    cfg: Configs,
) -> Dict:
    """
    Return bool indicating where the project (i.e. across
    both `local` and `central`) has consistent value lengths
    for sub and ses keys.
    It is not required that subjects and sessions have
    an equivalent value length (e.g.
    `sub-001`, `ses-01` is okay. But `sub-001`, `sub-02` is not.
    """
    folder_names = folders.get_all_sub_and_ses_names(cfg)

    subs_are_inconsistent = check_names_for_inconsistent_value_lengths(
        folder_names["sub"], "sub"
    )
    ses_are_inconsistent = check_names_for_inconsistent_value_lengths(
        folder_names["ses"], "ses"
    )
    return {"sub": subs_are_inconsistent, "ses": ses_are_inconsistent}
