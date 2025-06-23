from __future__ import annotations

import re
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs
    from datashuttle.utils.custom_types import (
        DisplayMode,
        Prefix,
        TopLevelFolder,
    )

from datetime import datetime
from itertools import chain
from pathlib import Path

from datashuttle.configs import canonical_configs, canonical_folders
from datashuttle.utils import formatting, getters, utils
from datashuttle.utils.custom_exceptions import NeuroBlueprintError

# -----------------------------------------------------------------------------
# Formatted Error Messages
# -----------------------------------------------------------------------------


def get_missing_prefix_error(name: str, prefix, path_: Path | None) -> str:
    """Return error message when a required prefix is missing from a name."""
    return handle_path(
        f"MISSING_PREFIX: The prefix {prefix} was not found in the name: {name}",
        path_,
    )


def get_bad_value_error(name: str, prefix, path_: Path | None) -> str:
    """Return error message when the value for a prefix is not an integer."""
    return handle_path(
        f"BAD_VALUE: The value for prefix {prefix} in name {name} is not an integer.",
        path_,
    )


def get_duplicate_prefix_error(name: str, prefix, path_: Path | None) -> str:
    """Return error message when a name contains multiple instances of the same prefix."""
    return handle_path(
        f"DUPLICATE_PREFIX: The name: {name} contains more than one instance of the prefix {prefix}.",
        path_,
    )


def get_name_error(name: str, prefix: Prefix, path_: Path | None) -> str:
    """Return error message when a name is invalid for a given prefix."""
    return handle_path(
        f"BAD_NAME: The name: {name} of type: {prefix} is not valid.", path_
    )


def get_special_char_error(name: str, path_: Path | None) -> str:
    """Return error message when a name contains invalid characters."""
    return handle_path(
        f"SPECIAL_CHAR: The name: {name}, contains characters which are not alphanumeric, dash or underscore.",
        path_,
    )


def get_name_format_error(name: str, path_: Path | None) -> str:
    """Return error message when a name does not follow key-value pair format."""
    return handle_path(
        f"NAME_FORMAT: The name {name} does not consist of key-value pairs separated by underscores.",
        path_,
    )


def get_value_length_error(prefix: Prefix) -> str:
    """Return error message for inconsistent value lengths for a prefix."""
    return f"VALUE_LENGTH: Inconsistent value lengths for the prefix: {prefix} were found in the project."


def get_datetime_error(key, name: str, strfmt: str, path_: Path | None) -> str:
    """Return error message when a datetime value is not in the expected ISO format."""
    return handle_path(
        f"DATETIME: Name {name} contains an invalid {key}. It should be ISO format: {strfmt}.",
        path_,
    )


def get_template_error(name: str, regexp: str, path_: Path | None) -> str:
    """Return error message when a name does not match a given template.

    The missing full-stop at the end is intentional, to avoid confusion when reading the regexp.
    """
    return handle_path(
        f"TEMPLATE: The name: {name} does not match the template: {regexp}",
        path_,
    )


def get_missing_top_level_folder_error(
    path_: Path | None, local_or_central: Literal["local", "central"]
) -> str:
    """Return error message when the top level folder is missing from the project."""
    return handle_path(
        f"TOP_LEVEL_FOLDER: The {local_or_central} project must contain a 'rawdata' or 'derivatives' folder.",
        path_,
    )


def get_duplicate_name_error(
    new_name: str, exist_name: str, exist_path: Path | None
) -> str:
    """Return error message when a new name duplicates an existing name."""
    return handle_path(
        f"DUPLICATE_NAME: The prefix for {new_name} duplicates the name: {exist_name}.",
        exist_path,
    )


def get_datatype_error(datatype_name: str, path_: Path | None) -> str:
    """Return error message when an invalid datatype name is encountered."""
    return handle_path(
        f"DATATYPE: {datatype_name} is not a valid datatype name.", path_
    )


def handle_path(message: str, path_: Path | None) -> str:
    """Append the file path to the error message if available."""
    if path_:
        message += f" Path: {path_.as_posix()}"
    return message


# -----------------------------------------------------------------------------
# Checking a standalone list of names
# -----------------------------------------------------------------------------


def validate_list_of_names(
    path_or_name_list: List[Path] | List[str],
    prefix: Prefix,
    name_templates: Optional[Dict] = None,
    check_value_lengths: bool = True,
) -> List[str]:
    """Validate a list of subject or session names against NeuroBlueprint.

    Parameters
    ----------
    path_or_name_list
        A list of pathlib.Path to NeuroBlueprint-formatted folders to validate

    prefix
        Whether these are subject (sub) or session (ses) level names

    name_templates
        A `name_template` dictionary to validate against. See `set_name_templates()`.

    check_value_lengths
        If `True`, check that the prefix-<value> value lengths
        are consistent across the passed list.

    Returns
    -------
    error_messages
        A list of found validation errors.

    """
    if len(path_or_name_list) == 0:
        return []

    error_messages = []

    # First, just validate each name individually
    for path_or_name in path_or_name_list:
        path_, name = get_path_and_name(path_or_name)

        error_messages += prefix_is_duplicate_or_has_bad_values(
            name, prefix, path_
        )
        error_messages += name_begins_with_bad_key(name, prefix, path_)
        error_messages += names_include_special_characters(name, path_)
        error_messages += dashes_and_underscore_alternate_incorrectly(
            name, path_
        )
        error_messages += datetime_are_iso_format(name, path_)
        error_messages += names_dont_match_templates(
            name, path_, prefix, name_templates
        )

    # Next, check interactions between names (e.g. duplicates,
    # inconsistent value lengths).  To do this we must strip names
    # in which the ids (e.g. sub-001) is invalid).
    # Note this called functions again loop over the list (O(n^2)) so
    # this is not very efficient but these lists should never be that long.
    stripped_path_or_names_list = strip_uncheckable_names(
        path_or_name_list, prefix
    )

    for path_or_name in stripped_path_or_names_list:
        path_, name = get_path_and_name(path_or_name)

        error_messages += new_name_duplicates_existing(
            name, stripped_path_or_names_list, prefix
        )

    if check_value_lengths:
        error_messages += value_lengths_are_inconsistent(
            stripped_path_or_names_list, prefix
        )

    return error_messages


def prefix_is_duplicate_or_has_bad_values(
    name: str, prefix: Prefix, path_: Path | None
) -> List[str]:
    """Check the sub- or ses- prefix.

    Ensure it is found only once in the name and
    that its value can be converted to integer.

    Parameters
    ----------
    name
        Name to check against template.

    prefix
        "sub" or "ses"

    path_
        Path to the folder that is being checked.

    Returns
    -------
        A list of validation errors.

    """
    value = re.findall(f"{prefix}(.*?)(?=_|$)", name)

    if len(value) == 0:
        return [get_missing_prefix_error(name, prefix, path_)]

    if len(value) > 1:
        return [get_duplicate_prefix_error(name, prefix, path_)]

    try:
        int(value[0])
        return []
    except ValueError:
        return [get_bad_value_error(name, prefix, path_)]


def new_name_duplicates_existing(
    new_name: str,
    existing_path_or_name_list: List[Path] | List[str],
    prefix: Prefix,
) -> List[str]:
    """Check that a subject or session value does not duplicate an existing value.

    The only case this is allowed is when the names match exactly.
    For example, if "sub-001" exists, we can pass "sub-001" as a valid subject name
    (for example, when making sessions). However, if "sub-001_another-tag" exists,
    we should throw an error, because this shares the same subject id but refers
    to a different subject.

    Parameters
    ----------
    new_name
        The name to check against all existing names.

    existing_path_or_name_list
        A list of existing names to check against.

    prefix
        "sub" or "ses"

    Returns
    -------
        A list of validation errors.

    """
    # Make a list of matches between `new_name` and any in `existing_names`
    new_name_id = utils.get_values_from_bids_formatted_name(
        [new_name], prefix, return_as_int=True
    )[0]

    error_messages = []
    for exist_path_or_name in existing_path_or_name_list:
        exist_path, exist_name = get_path_and_name(exist_path_or_name)

        exist_name_id = utils.get_values_from_bids_formatted_name(
            [exist_name], prefix, return_as_int=True
        )[0]

        if exist_name_id == new_name_id:
            if new_name != exist_name:
                message = get_duplicate_name_error(
                    new_name, exist_name, exist_path
                )
                error_messages.append(message)

    return error_messages


def names_dont_match_templates(
    name: str,
    path_: Path | None,
    prefix: Prefix,
    name_templates: Optional[Dict] = None,
) -> List[str]:
    """Validate a list of sub/ses names against the respective regexp `name_templates`.

    Parameters
    ----------
    name
        Name to check against template.

    path_
        Path to the folder that is being checked.

    prefix
        "sub" or "ses"

    name_templates
        Datashuttle's Name Templates dictionary defining the templates used.

    Returns
    -------
    A list of validation errors.

    """
    if name_templates is None:
        return []

    if name_templates["on"] is False:
        return []

    regexp = name_templates[prefix]

    if regexp is None:
        return []

    regexp = replace_tags_in_regexp(regexp)

    if not re.fullmatch(regexp, name):
        return [get_template_error(name, regexp, path_)]
    else:
        return []


def get_path_and_name(path_or_name: Path | str) -> Tuple[Optional[Path], str]:
    """Return the folder name from a Path (to the folder) or a str of the name itself."""
    if isinstance(path_or_name, Path):
        return path_or_name, path_or_name.name
    else:
        return None, path_or_name


def replace_tags_in_regexp(regexp: str) -> str:
    r"""Before validation, all tags in the names are converted to their final values.

    For example, (e.g. @DATE@ -> _date-<date>).
    We also want to allow template to be formatted like `sub-\d\d_@DATE@` as it is
    convenient for auto-completion in the TUI. Therefore, we must replace the tags
    in the regexp with their actual regexp equivalent before comparison.

    Note `replace_date_time_tags_in_name()` operates in place on a list.

    Parameters
    ----------
    regexp
        The name template regexp in which to replace tags.

    Returns
    -------
    The regexp with tags (e.g. @DATE@) formatted properly.

    """
    regexp_list = [regexp]
    date_regexp = r"\d\d\d\d\d\d\d\d"
    time_regexp = r"\d\d\d\d\d\d"

    formatting.replace_date_time_tags_in_name(
        regexp_list,
        datetime_with_key=formatting.format_datetime(date_regexp, time_regexp),
        date_with_key=formatting.format_date(date_regexp),
        time_with_key=formatting.format_time(time_regexp),
    )
    return regexp_list[0]


def name_begins_with_bad_key(
    name: str, prefix: Prefix, path_: Path | None
) -> List[str]:
    """Check that a list of NeuroBlueprint names begin with the required prefix (sub- or ses-).

    Parameters
    ----------
    name
        Name of the folder to validate.

    prefix
        "sub" or "ses".

    path_
        Path to the folder that is being validated.

    Returns
    -------
    A list of validation errors.

    """
    if name[:4] != f"{prefix}-":
        return [get_name_error(name, prefix, path_)]
    else:
        return []


def names_include_special_characters(
    name: str, path_: Path | None
) -> List[str]:
    """Check that a list of NeuroBlueprint formatted names do not contain special characters.

    Special characters are characters that are not integers, letters, dash or underscore.

    Parameters
    ----------
    name
        Name of the folder to validate

    path_
        Path of the folder that is being validated.

    Returns
    -------
    A list of validation errors.

    """
    if name_has_special_character(name):
        return [get_special_char_error(name, path_)]
    else:
        return []


def name_has_special_character(name: str) -> bool:
    """Return a bool indicating if the name contains special characters."""
    return not re.match("^[A-Za-z0-9_-]*$", name)


def dashes_and_underscore_alternate_incorrectly(
    name: str, path_: Path | None
) -> List[str]:
    """Check a list of names for expected Neuroblueprint underscore-dash order.

    Names should have the "-" and "-" ordered correctly. Names should be
    key-value pairs separated by underscores e.g. sub-001_ses-001.

    Parameters
    ----------
    name
        Name of the folder to validate

    path_
        Path of the folder that is being validated.

    Returns
    -------
    A list of validation errors.

    """
    discrim = {"-": 1, "_": -1}

    dashes_underscores = [discrim[ele] for ele in name if ele in ["-", "_"]]

    underscore_dash_not_interleaved = any(
        [ele == 0 for ele in utils.diff(dashes_underscores)]
    )

    if (
        not any(dashes_underscores)
        or dashes_underscores[0] != 1  # first must be -
        or dashes_underscores[-1] != 1  # last must be -
        or underscore_dash_not_interleaved
        or (name[-1] in discrim)  # name cannot end with - or _
    ):
        return [get_name_format_error(name, path_)]
    else:
        return []


def value_lengths_are_inconsistent(
    path_or_names_list: List[Path] | List[str] | List[Path | str],
    prefix: Prefix,
) -> List[str]:
    """Determine if there are inconsistent value lengths for the sub or ses key in a list of names.

    For example, ["sub-01", "sub-001"] is an error.

    Parameters
    ----------
    path_or_names_list
        A path of names of folders to validate, or path to folders to validate.

    prefix
        "sub" or "ses"

    Returns
    -------
    A list of validation errors.

    """
    names_list = [
        path_or_name if isinstance(path_or_name, str) else path_or_name.name
        for path_or_name in path_or_names_list
    ]

    prefix_values = utils.get_values_from_bids_formatted_name(
        names_list, prefix, return_as_int=False
    )

    value_len = [len(value) for value in prefix_values]

    inconsistent_value_len = value_len != [] and not utils.all_identical(
        value_len
    )

    error_messages = []
    if inconsistent_value_len:
        message = get_value_length_error(prefix)
        error_messages.append(message)

    return error_messages


def datetime_are_iso_format(
    name: str,
    path_: Path | None,
) -> List[str]:
    """Check formatting for date-, time-, or datetime- tags.

    Parameters
    ----------
    name
        Name of the folder to validate

    path_
        Path of the folder that is being validated.

    Returns
    -------
    error_message
        A list of validation errors.

    """
    formats = {
        "datetime": "%Y%m%dT%H%M%S",
        "time": "%H%M%S",
        "date": "%Y%m%d",
    }

    key = next((key for key in formats if key in name), None)

    error_message: List[str]
    if not key:
        error_message = []

    else:
        try:
            format_to_check = utils.get_values_from_bids_formatted_name(
                [name], key, return_as_int=False
            )[0]
        except:
            return []

        strfmt = formats[key]

        try:
            datetime.strptime(format_to_check, strfmt)
            error_message = []
        except ValueError:
            error_message = [get_datetime_error(key, name, strfmt, path_)]

    return error_message


def raise_display_mode(
    message: str, display_mode: DisplayMode, log: bool
) -> None:
    """Show a message by raising an error, displaying warning, or printing.

    Optionally log with the current datashuttle logger.

    Parameters
    ----------
    message
        Message to display.

    display_mode
        Mode to display, "error", "warn" or "print".

    log
        If `True`, log the message.

    """
    if display_mode == "error":
        utils.log_and_raise_error(message, NeuroBlueprintError)

    elif display_mode == "warn":
        utils.warn(message, log=log)

    elif display_mode == "print":
        if log:
            utils.log_and_message(message)
        else:
            utils.print_message_to_user(message)
    else:
        raise ValueError(
            "`display_mode` must be either 'error', 'warn' or 'print'."
        )


# -----------------------------------------------------------------------------
# Validate Entire Project
# -----------------------------------------------------------------------------


def validate_project(
    cfg: Configs,
    top_level_folder_list: List[TopLevelFolder],
    include_central: bool = False,
    display_mode: DisplayMode = "error",
    log: bool = True,
    name_templates: Optional[Dict] = None,
    strict_mode: bool = False,
) -> List[str]:
    """Validate all subject and session folders within a project.

    Parameters
    ----------
    cfg
        datashuttle Configs class.

    top_level_folder_list
        The top level folders to validate.

    include_central
        If `False`, only project folders in the `local_path` will
        be validated. Otherwise, project folders in both the `local_path`
        and `central_path` will be validated.

    display_mode
        Determine whether error or warning is raised.

    log
        If `True`, errors or warnings are logged to "datashuttle" logger.

    name_templates
        A `name_template` dictionary to validate against. See `set_name_templates()`.

    strict_mode
        If `True`, only allow NeuroBlueprint-formatted folders to exist in
        the project. By default, non-NeuroBlueprint folders (e.g. a folder
        called 'my_stuff' in the 'rawdata') are allowed, and only folders
        starting with sub- or ses- prefix are checked. In `Strict Mode`,
        any folder not prefixed with sub-, ses- or a valid datatype will
        raise a validation issue.

    Returns
    -------
    error_messages
        A list of validation errors.

    """
    error_messages = []

    # Check basic things about the project (e.g. contains a top-level folder)
    error_messages += check_high_level_project_structure(cfg, include_central)

    for top_level_folder in top_level_folder_list:
        if strict_mode:
            error_messages += check_strict_mode(
                cfg, top_level_folder, include_central
            )

        # Get a list of paths to every sub- or ses- folder
        folder_paths = getters.get_all_sub_and_ses_paths(
            cfg,
            top_level_folder,
            include_central,
        )

        # Check subject folders are valid
        error_messages += validate_list_of_names(
            folder_paths["sub"],
            prefix="sub",
            name_templates=name_templates,
        )

        # Sessions a little more complicated. We need to check
        # for session duplicates separately for each subject.
        # However, we need to check inconsistent ses-<value> lengths
        # across the entire project.

        # Check all names as well as duplicates per-subject
        for ses_paths in folder_paths["ses"].values():
            error_messages += validate_list_of_names(
                ses_paths,
                "ses",
                check_value_lengths=False,
                name_templates=name_templates,
            )

        # Next, check inconsistent value lengths across the entire project
        all_ses_paths = list(chain(*folder_paths["ses"].values()))

        stripped_ses_paths = strip_uncheckable_names(all_ses_paths, "ses")
        error_messages += value_lengths_are_inconsistent(
            stripped_ses_paths, "ses"
        )

    # Display the collected errors using the selected method
    if any(error_messages):
        for message in error_messages:
            raise_display_mode(message, display_mode, log)
    else:
        utils.print_message_to_user("No validation issues detected.")

    return error_messages


def validate_names_against_project(
    cfg: Configs,
    top_level_folder: TopLevelFolder,
    sub_names: List[str],
    ses_names: Optional[List[str]] = None,
    include_central: bool = False,
    display_mode: DisplayMode = "error",
    log: bool = True,
    name_templates: Optional[Dict] = None,
) -> None:
    """Check that sub / ses names are formatted consistently with the rest of the project.

    This is used for creating folders.

    Unfortunately this is quite fiddly, as it is important to only
    validate the passed list of subject / session names while ignoring
    validation errors that may already exist in the project.

    Parameters
    ----------
    cfg
        datashuttle Configs class.

    top_level_folder
        The top level folder to validate

    sub_names
        A list of subject-level names to validate against the
        subject names that exist in the project.

    ses_names
        A list of session-level names to validate against the
        session names that exist in the project. Note that
        duplicate checks will only be performed for sessions within
        the passed `sub_names`.

    include_central
        If `True`, only project folders in the `local_path` will
        be validated against. Otherwise, project folders in both the
        `local_path` and `central_path` will be validated against.

    display_mode
        Determine whether error or warning is raised.

    log
        If `True`, errors or warnings are logged to "datashuttle" logger.

    name_templates
        A `name_template` dictionary to validate against. See `set_name_templates()`.

    """
    error_messages = []

    # First, check the list of passed names are valid
    error_messages += validate_list_of_names(
        sub_names,
        prefix="sub",
        name_templates=name_templates,
    )

    # Next, get all of the subjects and sessions from
    # the project (local and possibly central)
    folder_paths = getters.get_all_sub_and_ses_paths(
        cfg, top_level_folder, include_central
    )

    if folder_paths["sub"]:
        # Strip any totally invalid names which we can't extract
        # the sub integer value for the following checks
        valid_sub_names = strip_uncheckable_names(sub_names, "sub")
        valid_sub_in_project = strip_uncheckable_names(
            folder_paths["sub"], "sub"
        )

        # Check list of passed names against all the names in the project
        # for value-length violations and duplicates.
        if any(value_lengths_are_inconsistent(valid_sub_in_project, "sub")):
            error_messages += [
                "Cannot check names for inconsistent value lengths "
                "because the subject value lengths are not consistent "
                "across the project."
            ]
        else:
            error_messages += value_lengths_are_inconsistent(
                valid_sub_names + valid_sub_in_project, "sub"
            )

        for new_sub in valid_sub_names:
            error_messages += new_name_duplicates_existing(
                new_sub, valid_sub_in_project, "sub"
            )

    # Now we need to check the sessions.
    if ses_names is not None and any(ses_names):
        # First, validate the list of passed session names
        error_messages += validate_list_of_names(
            ses_names, "ses", name_templates=name_templates
        )

        if folder_paths["sub"]:
            # Next, we need to check that the passed session names
            # do not duplicate existing session names and
            # that do not create inconsistent ses-<value> lengths across the project.
            valid_ses_names = strip_uncheckable_names(ses_names, "ses")

            # First, we need to check for duplicate session names
            # for each subject separately, as duplicate session names
            # are allowed across different subjects (but not within a single sub).
            for new_sub in sub_names:
                if new_sub in folder_paths["ses"]:
                    valid_ses_in_sub = strip_uncheckable_names(
                        folder_paths["ses"][new_sub],
                        "ses",
                    )
                    for new_ses in valid_ses_names:
                        error_messages += new_name_duplicates_existing(
                            new_ses, valid_ses_in_sub, "ses"
                        )
            # Next, we need to check for inconsistent session value lengths
            # across the entire project at once (because inconsistent
            # ses-<value> lengths are not allowed across different subs).
            all_ses_paths = list(chain(*folder_paths["ses"].values()))

            all_valid_ses = strip_uncheckable_names(
                all_ses_paths,
                "ses",
            )

            if any(value_lengths_are_inconsistent(all_valid_ses, "ses")):
                error_messages += [
                    "Cannot check names for inconsistent value lengths "
                    "because the session value lengths for this project "
                    "are not consistent."
                ]
            else:
                error_messages += value_lengths_are_inconsistent(
                    valid_ses_names + all_valid_ses, "ses"
                )

    # Display the collected errors using the selected method
    for message in error_messages:
        raise_display_mode(message, display_mode, log)


def check_high_level_project_structure(
    cfg: Configs, include_central: bool
) -> List[str]:
    """Perform basic validation checks on the project structure.

    This includes checking that the project folder name is valid, and that the
    project folder contains either a "rawdata" or "derivatives" folder.

    Parameters
    ----------
    cfg
        Datashuttle Configs class.

    include_central
        If `True`, the central project is also checked.

    Returns
    -------
    error_messages
        A list of validation errors.

    """
    # To avoid circular imports
    from datashuttle.utils.folders import search_for_folders

    error_messages = []

    # Check the project name
    if any(names_include_special_characters(cfg["local_path"].name, None)):
        error_messages += [
            f"PROJECT_NAME: The local project name folder {cfg['local_path'].name} "
            f"contains non-alphanumeric characters. Path: {cfg['local_path']}"
        ]

    if cfg["central_path"]:
        if any(
            names_include_special_characters(cfg["central_path"].name, None)
        ):
            error_messages += [
                f"PROJECT_NAME: The central project name folder {cfg['central_path'].name} "
                f"contains non-alphanumeric characters. Path: {cfg['central_path']}"
            ]

    # Check the local project folder contains rawdata or derivatives
    if (
        not (cfg["local_path"] / "rawdata").is_dir()
        and not (cfg["local_path"] / "derivatives").is_dir()
    ):
        message = get_missing_top_level_folder_error(
            cfg["local_path"], "local"
        )
        error_messages.append(message)

    if not include_central:
        return error_messages

    # Check the central project folder contains rawdata for derivatives
    all_folder_names, all_filenames = search_for_folders(
        cfg,
        cfg["central_path"],
        "central",
        "*",
        verbose=False,
        return_full_path=False,
    )

    if ("rawdata" not in all_folder_names) and (
        "derivatives" not in all_folder_names
    ):
        message = get_missing_top_level_folder_error(
            cfg["central_path"], "central"
        )
        error_messages.append(message)

    return error_messages


def check_strict_mode(
    cfg: Configs, top_level_folder: TopLevelFolder, include_central: bool
) -> List[str]:
    """Perform `strict_mode`  validation.

    `strict_mode` does not allow any non-NeuroBlueprint folder to exist
    in the project outside the datatype folder. NeuroBlueprint folders
    are top-level folder or folder with sub-, ses- or datatype.

    The reason for `strict_mode` is that NeuroBlueprint does allow other
    folders to be in the project, but their existence means we cannot check
    prefix typos and other issues (e.g. if subs-extra is a folder, or "rat1",
    how do we know if it is intended to be a subject folder and validate it,
    or just an auxiliary folder.

    Parameters
    ----------
    cfg
        Datashuttle Configs class.

    top_level_folder
        "rawdata" or "derivatives".

    include_central
        If `True`, the central project is also checked.

    Returns
    -------
    error_messages
        A list of validation errors.

    """
    # For circular imports
    from datashuttle.utils import folders

    if include_central:
        raise ValueError(
            "`strict_mode` is currently only available for `include_central=False`."
        )

    error_messages = []

    sub_level_folder_paths = folders.search_project_for_sub_or_ses_names(
        cfg,
        top_level_folder,
        None,
        "*",
        include_central=False,
        return_full_path=True,
    )

    for sub_level_path in sub_level_folder_paths["local"]:
        # Check all folders found in a top-level folder are
        # sub- prefixed folders.
        sub_level_name = sub_level_path.name

        if sub_level_name[:4] != "sub-":
            message = get_name_error(sub_level_name, "sub", sub_level_path)
            error_messages.append(message)
            continue

        ses_level_folder_paths = folders.search_project_for_sub_or_ses_names(
            cfg,
            top_level_folder,
            sub_level_name,
            "*",
            include_central=False,
            return_full_path=True,
        )

        for ses_level_path in ses_level_folder_paths["local"]:
            # For each sub- prefixed folder, check that all folders within
            # the subject folder are ses- prefixed folders.
            ses_level_name = ses_level_path.name

            if ses_level_name[:4] != "ses-":
                message = get_name_error(ses_level_name, "ses", ses_level_path)
                error_messages.append(message)

            base_folder = cfg.get_base_folder("local", top_level_folder)

            search_results: List[Path]
            search_results = folders.search_sub_or_ses_level(  # type: ignore
                cfg,
                base_folder,
                "local",
                sub_level_name,
                ses_level_name,
                return_full_path=True,
            )[0]

            canonical_datatypes = canonical_configs.get_datatypes()
            for datatype_level_path in search_results:
                # For each ses- prefixed folder, check that
                # only valid datatypes are included within it.
                datatype_level_name = datatype_level_path.name

                if datatype_level_name not in canonical_datatypes:
                    message = get_datatype_error(
                        datatype_level_name, datatype_level_path
                    )
                    error_messages.append(message)

    return error_messages


@overload
def strip_uncheckable_names(
    path_or_names_list: List[Path],
    prefix: Prefix,
) -> List[Path]: ...


@overload
def strip_uncheckable_names(
    path_or_names_list: List[str],
    prefix: Prefix,
) -> List[str]: ...


def strip_uncheckable_names(
    path_or_names_list: List[Path] | List[str],
    prefix: Prefix,
) -> List[Path] | List[str]:
    """Remove any name in which the `prefix` value (sub or ses typically) cannot be converted into an integer.

    This is necessary as some validation steps (e.g. checking duplicate names)
    requires conversion to `int` and will fail for this reason if
    these bad names are not removed.

    Parameters
    ----------
    path_or_names_list
        A path of names of folders to validate, or path to folders to validate.

    prefix
        "sub" or "ses".

    Returns
    -------
    List of path or names which the uncheckable ones (e.g. that are too broken
    to be validated against) removed.

    """
    new_list = []

    for path_or_name in path_or_names_list:
        path_, name = get_path_and_name(path_or_name)

        try:
            utils.get_values_from_bids_formatted_name(
                [name], prefix, return_as_int=True
            )[0]
        except BaseException:
            continue

        if path_:
            new_list.append(path_)
        else:
            new_list.append(name)  # type: ignore

    return new_list


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------


def check_datatypes_are_valid(
    datatype: Union[List[str], str], allow_all: bool = False
) -> str | None:
    """Check a datatype of list of datatypes is a valid NeuroBlueprint datatype.

    Parameters
    ----------
    datatype
        A str or a list of str where str is a NeuroBlueprint datatype.

    allow_all
        At this stage, "all" may still be included in the list of datatypes.
        This is valid in some cases as it indicates all datatypes.

    Returns
    -------
    message
        An error message or None if no errors found.

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
        return message

    return None
