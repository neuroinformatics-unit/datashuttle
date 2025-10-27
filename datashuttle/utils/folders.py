from __future__ import annotations

import json
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

if TYPE_CHECKING:
    from collections.abc import ItemsView

    from datashuttle.configs.config_class import Configs
    from datashuttle.utils.custom_types import TopLevelFolder

import fnmatch
import re
from datetime import datetime
from pathlib import Path

from datashuttle.configs import canonical_folders, canonical_tags
from datashuttle.utils import rclone, utils, validation
from datashuttle.utils.custom_exceptions import NeuroBlueprintError
from datashuttle.utils.utils import get_values_from_bids_formatted_name

# -----------------------------------------------------------------------------
# Create Folders
# -----------------------------------------------------------------------------


def create_folder_trees(
    cfg: Configs,
    top_level_folder: TopLevelFolder,
    sub_names: Union[str, list],
    ses_names: Union[str, list],
    datatype: Union[List[str], str],
    log: bool = True,
) -> Dict[str, List[Path]]:
    """Entry method to make a full folder tree.

    Iterate through all passed subjects, then sessions, then
    subfolders within a datatype folder. This
    permits flexible creation of folders (e.g.
    to make subject only, do not pass session name.

    Ensure sub and ses names are already formatted
    before use in this function (see _start_log())

    Parameters
    ----------
    cfg
        datashuttle config UserDict

    top_level_folder
        either "rawdata" or "derivatives"

    sub_names, ses_names, datatype
        see create_folders()

    log
        whether to log or not. If True, logging must
        already be initialised.

    """
    datatype_passed = datatype not in [[""], ""]

    if "all" in datatype or datatype == "all":
        raise ValueError(
            "Using 'all' keyboard for `create_folders` "
            "datatype is deprecated in 0.6.0"
        )

    # Initialize all_paths with required keys
    all_paths: dict = {
        "sub": [],
        "ses": [],
    }

    if datatype_passed:
        error_message = validation.check_datatypes_are_valid(
            datatype, allow_all=True
        )
        if error_message:
            utils.log_and_raise_error(error_message, NeuroBlueprintError)

    for sub in sub_names:
        sub_path = cfg.build_project_path(
            "local",
            sub,
            top_level_folder,
        )

        create_folders(sub_path, log)

        if not any(ses_names):
            all_paths["sub"].append(sub_path)
            continue

        for ses in ses_names:
            ses_path = cfg.build_project_path(
                "local",
                [sub, ses],
                top_level_folder,
            )

            create_folders(ses_path, log)

            if datatype_passed:
                make_datatype_folders(
                    cfg,
                    datatype,
                    ses_path,
                    "ses",
                    save_paths=all_paths,
                    log=log,
                )
            else:
                all_paths["ses"].append(ses_path)

    return all_paths


def make_datatype_folders(
    cfg: Configs,
    datatype: Union[list, str],
    sub_or_ses_level_path: Path,
    level: str,
    save_paths: Dict,
    log: bool = True,
):
    """Make datatype folder (e.g. behav) at the sub or ses level.

    Checks folder_class.Folders attributes, whether the datatype
    is used and at the current level.

    Parameters
    ----------
    cfg
        datashuttle configs

    datatype
        datatype (e.g. "behav", "all") to use. Use
        empty string ("") for none.

    sub_or_ses_level_path
        Full path to the subject
        or session folder where the new folder
        will be written.

    level
        The folder level that the
        folder will be made at, "sub" or "ses"

    save_paths
        A dictionary, which will be filled
        with created paths split by datatype name.

    log
        whether to log on or not (if True, logging must
        already be initialised).

    """
    datatype_items = cfg.get_datatype_as_dict_items(datatype)

    for datatype_key, datatype_folder in datatype_items:  # type: ignore
        if datatype_folder.level == level:
            datatype_name = datatype_folder.name

            datatype_path = sub_or_ses_level_path / datatype_name

            create_folders(datatype_path, log)

            # Use the custom datatype names for the output.
            if datatype_name in save_paths:
                save_paths[datatype_name].append(datatype_path)
            else:
                save_paths[datatype_name] = [datatype_path]


# Create Folders Helpers --------------------------------------------------------


def create_folders(paths: Union[Path, List[Path]], log: bool = True) -> None:
    """Make a path or list of paths if they do not already exist.

    Parameters
    ----------
    paths
        Path or list of Paths to create

    log
        if True, log all made folders. This
        requires the logger to already be initialised.

    """
    if isinstance(paths, Path):
        paths = [paths]

    for path_ in paths:
        if not path_.is_dir():
            path_.mkdir(parents=True)
            if log:
                utils.log(f"Made folder at path: {path_}")


# -----------------------------------------------------------------------------
# Search Existing Folders
# -----------------------------------------------------------------------------

# Search Subjects / Sessions
# -----------------------------------------------------------------------------


def search_project_for_sub_or_ses_names(
    cfg: Configs,
    top_level_folder: TopLevelFolder,
    sub: Optional[str],
    search_str: str,
    include_central: bool,
    return_full_path: bool = False,
) -> Dict:
    """If sub is None, the top-level level folder will be searched (i.e. for subjects).

    The search string "sub-*" is suggested in this case. Otherwise, the subject,
    level folder for the specified subject will be searched.
    The search_str "ses-*" is suggested in this case.

    Note `verbose` argument of `search_sub_or_ses_level()` is set to `False`,
    as session folders for local subjects that are not yet on central
    will be searched for on central, showing a confusing 'folder not found'
    message.

    Parameters
    ----------
    cfg
        Datashuttle Configs object.

    top_level_folder
        "rawdata" or "derivatives".

    sub
        Subject name (if provided, search for a session within that sub)

    search_str
        Glob-style search to perform e.g. "sub-*"

    include_central
        If `True`, central project is also searched.

    return_full_path
        If True, the full path to the discovered folders is provided.
        Otherwise, just the name.

    Returns
    -------
    A dictionary with "local" and "central" keys, where values
    are the discovered folders. "central" is `None` if include_central is `False`.

    """
    # Search local and central for folders that begin with "sub-*"
    local_foldernames, _ = search_sub_or_ses_level(  # type: ignore
        cfg,
        cfg.get_base_folder("local", top_level_folder),
        "local",
        sub=sub,
        search_str=search_str,
        verbose=False,
        return_full_path=return_full_path,
    )

    central_foldernames: List

    if include_central:
        central_foldernames, _ = search_sub_or_ses_level(  # type: ignore
            cfg,
            cfg.get_base_folder("central", top_level_folder),
            "central",
            sub,
            search_str=search_str,
            verbose=False,
            return_full_path=return_full_path,
        )
    else:
        central_foldernames = []

    return {"local": local_foldernames, "central": central_foldernames}


# Search Data Types
# -----------------------------------------------------------------------------


def items_from_datatype_input(
    cfg: Configs,
    local_or_central: str,
    top_level_folder: TopLevelFolder,
    datatype: Union[list, str],
    sub: str,
    ses: Optional[str] = None,
) -> Union[ItemsView, zip]:
    """Return the list of datatypes to transfer.

    Take these directly from user input, or by searching
    what is available if "all" is passed.

    see _transfer_datatype() for full parameters list.

    Returns
    -------
    Datatypes as a dictionary items() or zip that mimics that structure.
    The dictionary is in the form datatype name: Folder() struct.
    See `canonical_folders.py`.

    """
    base_folder = cfg.get_base_folder(local_or_central, top_level_folder)

    if datatype not in [
        "all",
        ["all"],
        "all_datatype",
        ["all_datatype"],
    ]:
        datatype_items = cfg.get_datatype_as_dict_items(
            datatype,
        )
    else:
        datatype_items = search_for_datatype_folders(
            cfg,
            base_folder,
            local_or_central,
            sub,
            ses,
        )

    return datatype_items


def search_for_datatype_folders(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    sub: str,
    ses: Optional[str] = None,
) -> zip:
    """Search a subject or session folder specifically for datatypes.

    First searches for all folders / files
    in the folder, and then returns any folders that
    match datatype name.

    see folders.search_sub_or_ses_level() for full
    parameters list.

    Returns
    -------
    Find the datatype files and return in
    a format that mirrors dict.items()

    """
    search_results = search_sub_or_ses_level(
        cfg, base_folder, local_or_central, sub, ses
    )[0]

    data_folders = process_glob_to_find_datatype_folders(
        search_results,
        canonical_folders.get_datatype_folders(),
    )
    return data_folders


def process_glob_to_find_datatype_folders(
    folder_names: list,
    datatype_folders: dict,
) -> zip:
    """Process the results of glob on a sub or session level.

    The results could contain any type of folder / file.
    see project.search_sub_or_ses_level() for inputs.

    Returns
    -------
    Find the datatype files and return in
    a format that mirrors dict.items()

    """
    ses_folder_keys = []
    ses_folder_values = []
    for name in folder_names:
        datatype_key = [
            key
            for key, value in datatype_folders.items()
            if value.name == name
        ]

        if datatype_key:
            ses_folder_keys.append(datatype_key[0])
            ses_folder_values.append(datatype_folders[datatype_key[0]])

    return zip(ses_folder_keys, ses_folder_values)


# -----------------------------------------------------------------------------
# Wildcards
# -----------------------------------------------------------------------------


def search_with_tags(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    all_names: List[str],
    sub: Optional[str] = None,
) -> List[str]:
    """Handle wildcard and datetime range searching in names during upload or download.

    There are two types of special patterns that can be used in names:
    1. Wildcards: Names containing @*@ will be replaced with "*" for glob pattern matching
    2. Datetime ranges: Names containing @DATETO@, @TIMETO@, or @DATETIMETO@ will be used
       to filter folders within a specific datetime range

    For datetime ranges, the format must be:
    - date: YYYYMMDD@DATETO@YYYYMMDD (e.g., "20240101@DATETO@20241231")
    - time: HHMMSS@TIMETO@HHMMSS (e.g., "000000@TIMETO@235959")
    - datetime: YYYYMMDDTHHMMSS@DATETIMETO@YYYYMMDDTHHMMSS

    Parameters
    ----------
    cfg
        datashuttle project configuration
    base_folder
        folder to search for wildcards in
    local_or_central
        "local" or "central" project path to search in
    all_names
        list of names that may contain wildcards or datetime ranges. If sub is
        passed, these are treated as session names. If sub is None, they are
        treated as subject names
    sub
        optional subject to search for sessions in. If not provided,
        will search for subjects rather than sessions

    Returns
    -------
    List[str]
        A list of matched folder names after wildcard expansion and datetime filtering.
        For datetime ranges, only folders with timestamps within the specified range
        will be included.

    Examples
    --------
    Wildcards:
        search_with_tags(cfg, path, "local", ["sub-@*@"])
        ["sub-001", "sub-002", "sub-003"]

    Date range:
        search_with_tags(
            cfg, path, "local", ["sub-001_20240101@DATETO@20241231_id-*"]
        )
        ["sub-001_date-20240315_id-1", "sub-001_date-20240401_id-2"]

    Time range:
        search_with_tags(cfg, path, "local", ["sub-002_000000@TIMETO@120000"])
        ["sub-002_time-083000", "sub-002_time-113000"]

    """
    new_all_names: List[str] = []

    for name in all_names:
        if not (
            canonical_tags.tags("*") in name
            or canonical_tags.tags("DATETO") in name
            or canonical_tags.tags("TIMETO") in name
            or canonical_tags.tags("DATETIMETO") in name
        ):
            # If no special tags, just add the name as is
            new_all_names.append(name)
            continue

        # Handle wildcard replacement first if present
        search_str = name
        if canonical_tags.tags("*") in name:
            search_str = search_str.replace(canonical_tags.tags("*"), "*")

        # Handle datetime ranges
        format_type = None
        tag = None

        if canonical_tags.tags("DATETO") in search_str:
            tag = canonical_tags.tags("DATETO")
            format_type = "date"
        elif canonical_tags.tags("TIMETO") in search_str:
            tag = canonical_tags.tags("TIMETO")
            format_type = "time"
        elif canonical_tags.tags("DATETIMETO") in search_str:
            tag = canonical_tags.tags("DATETIMETO")
            format_type = "datetime"

        if format_type is not None:
            assert tag is not None
            search_str = format_and_validate_datetime_search_str(
                search_str, format_type, tag
            )

            # Use the helper function to perform the glob search
            if sub:
                matching_names = search_sub_or_ses_level(
                    cfg,
                    base_folder,
                    local_or_central,
                    sub,
                    search_str=search_str,
                )[0]
            else:
                matching_names = search_sub_or_ses_level(
                    cfg, base_folder, local_or_central, search_str=search_str
                )[0]

            # Filter results by datetime range
            start_timepoint, end_timepoint = (
                strip_start_end_date_from_datetime_tag(name, format_type, tag)
            )
            matching_names = filter_names_by_datetime_range(
                matching_names, format_type, start_timepoint, end_timepoint
            )
            new_all_names.extend(matching_names)
        else:
            # No datetime range, just perform the glob search with wildcards
            if sub:
                matching_names = search_sub_or_ses_level(
                    cfg,
                    base_folder,
                    local_or_central,
                    sub,
                    search_str=search_str,
                )[0]
            else:
                matching_names = search_sub_or_ses_level(
                    cfg, base_folder, local_or_central, search_str=search_str
                )[0]
            new_all_names.extend(matching_names)

    return list(set(new_all_names))  # Remove duplicates


def filter_names_by_datetime_range(
    names: List[str],
    format_type: str,
    start_timepoint: datetime,
    end_timepoint: datetime,
) -> List[str]:
    """Filter a list of names based on a datetime range.

    Assumes all names contain the format_type pattern (e.g., date-*, time-*)
    as they were searched using this pattern.

    Parameters
    ----------
    names
        List of names to filter, all containing the datetime pattern
    format_type
        One of "datetime", "time", or "date"
    start_timepoint
        Start of the datetime range
    end_timepoint
        End of the datetime range

    Returns
    -------
    List[str]
        Filtered list of names that fall within the datetime range

    Raises
    ------
    ValueError
        If any datetime value does not match the expected ISO format

    """
    filtered_names: List[str] = []
    for candidate in names:
        candidate_basename = (
            candidate if isinstance(candidate, str) else candidate.name
        )
        value = get_values_from_bids_formatted_name(
            [candidate_basename], format_type
        )[0]

        try:
            candidate_timepoint = datetime_object_from_string(
                value, format_type
            )
        except ValueError:
            utils.log_and_raise_error(
                f"Invalid {format_type} format in name {candidate_basename}. "
                f"Expected ISO format: {canonical_tags.get_datetime_formats()[format_type]}",
                ValueError,
            )

        if start_timepoint <= candidate_timepoint <= end_timepoint:
            filtered_names.append(candidate)

    return filtered_names


# -----------------------------------------------------------------------------
# Datetime Tag Functions
# -----------------------------------------------------------------------------


def get_datetime_to_search_regexp(format_type: str, tag: str) -> str:
    r"""Get the full regexp to find the full @DATETIMETO@ and similar tags.

    Users will write "<date>@DATETO@<date>", "<time>@TIMETO@<time>",
    or "<datetime>@DATETIMETO@<datetime>". This creates the full regexp for finding
    this string.

    Parameters
    ----------
    format_type
        One of "datetime", "time", or "date"

    tag
        The tag used for the range (e.g. @DATETIMETO@)

    Returns
    -------
    full_tag_regex
        The full regexp to search for e.g.
        "\d{8}T\d{6}@DATETIMETO@\d{8}T\d{6}"

    """
    if format_type == "date":
        regexp = "\d{8}"

    elif format_type == "time":
        regexp = "\d{6}"

    elif format_type == "datetime":
        regexp = "\d{8}T\d{6}"

    full_tag_regex = rf"({regexp}){re.escape(tag)}({regexp})"

    return full_tag_regex


def find_datetime_in_name(
    name: str, format_type: str, tag: str
) -> tuple[str | Any, ...] | None:
    """Find and extract datetime values from a name using a regex pattern.

    Parameters
    ----------
    name
        The name containing the datetime range
        e.g. "sub-001_20240101@DATETO@20250101_id-*"
    format_type
        One of "datetime", "time", or "date"
    tag
        The tag used for the range (e.g. @DATETO@)

    Returns
    -------
    tuple[str, str] | None
        A tuple containing (start_datetime_str, end_datetime_str) if found,
        None if no match is found

    """
    full_tag_regex = get_datetime_to_search_regexp(format_type, tag)

    match = re.search(full_tag_regex, name)

    return match.groups() if match else None


def strip_start_end_date_from_datetime_tag(
    search_str: str, format_type: str, tag: str
) -> tuple[datetime, datetime]:
    """Extract and validate start and end datetime values from a search string.

    Parameters
    ----------
    search_str
        The search string containing the datetime range
        e.g. "sub-001_20240101T000000@DATETIMETO@20250101T235959"
    format_type
        One of "datetime", "time", or "date"
    tag
        The tag used for the range (e.g. @DATETIMETO@)

    Returns
    -------
    tuple[datetime, datetime]
        A tuple containing (start_timepoint, end_timepoint)

    Raises
    ------
    NeuroBlueprintError
        If the datetime format is invalid, the range is malformed,
        or end datetime is before start datetime

    """
    full_tag_regex = get_datetime_to_search_regexp(format_type, tag)

    match = re.search(full_tag_regex, search_str)

    if not match:
        utils.log_and_raise_error(
            f"Invalid {format_type} range format in search string: {search_str}. Ensure the format matches the expected pattern: {canonical_tags.get_datetime_formats()[format_type]}.",
            NeuroBlueprintError,
        )

    assert match is not None, "type narrow `match`"
    start_str, end_str = match.groups()

    try:
        start_timepoint = datetime_object_from_string(start_str, format_type)
        end_timepoint = datetime_object_from_string(end_str, format_type)
    except ValueError as e:
        utils.log_and_raise_error(
            f"Invalid {format_type} format in search string: {search_str}. Error: {str(e)}",
            NeuroBlueprintError,
        )

    if end_timepoint < start_timepoint:
        utils.log_and_raise_error(
            f"End {format_type} is before start {format_type}. Ensure the end datetime is after the start datetime.",
            NeuroBlueprintError,
        )

    return start_timepoint, end_timepoint


def format_and_validate_datetime_search_str(
    search_str: str, format_type: str, tag: str
) -> str:
    """Validate and format a search string containing a datetime range.

    Parameters
    ----------
    search_str
        The search string containing the datetime range
        e.g. "sub-001_20240101@DATETO@20250101_id-*" or "sub-002_000000@TIMETO@235959"
    format_type
        One of "datetime", "time", or "date"
    tag
        The tag used for the range (e.g. @DATETO@)

    Returns
    -------
    str
        The formatted search string with datetime range replaced
        e.g. "sub-001_date-*_id-*" or "sub-002_time-*"

    Raises
    ------
    NeuroBlueprintError
        If the datetime format is invalid or the range is malformed

    """
    # Validate the datetime range format
    strip_start_end_date_from_datetime_tag(search_str, format_type, tag)

    # Replace datetime range with wildcard pattern
    full_tag_regex = get_datetime_to_search_regexp(format_type, tag)

    full_search_str = re.sub(full_tag_regex, f"{format_type}-*", search_str)

    already_has_wildcard_at_end = re.search(
        rf"{full_tag_regex}(?=\*)", search_str
    )

    if already_has_wildcard_at_end:
        # Handle edge case where @*@ tag is immediately after @DATETIMETO@
        # or similar tag. This results in "datetime-**" which cases errors.
        full_search_str = full_search_str.replace("**", "*")

    return full_search_str


def datetime_object_from_string(
    datetime_string: str, format_type: str
) -> datetime:
    """Convert a datetime string to a datetime object using the appropriate format.

    Parameters
    ----------
    datetime_string :
        The string to convert to a datetime object

    format_type :
        One of "datetime", "time", or "date"

    Returns
    -------
    datetime
        The parsed datetime object

    Raises
    ------
    ValueError
        If the string cannot be parsed using the specified format

    """
    return datetime.strptime(
        datetime_string, canonical_tags.get_datetime_formats()[format_type]
    )


# -----------------------------------------------------------------------------
# Low level search functions
# -----------------------------------------------------------------------------


@overload
def search_sub_or_ses_level(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    sub: Optional[str] = ...,
    ses: Optional[str] = ...,
    search_str: str = ...,
    verbose: bool = ...,
    return_full_path: Literal[False] = ...,
) -> Tuple[List[str], List[str]]: ...


@overload
def search_sub_or_ses_level(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    sub: Optional[str] = ...,
    ses: Optional[str] = ...,
    search_str: str = ...,
    verbose: bool = ...,
    return_full_path: Literal[True] = ...,
) -> Tuple[List[Path], List[str]]: ...


def search_sub_or_ses_level(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    sub: Optional[str] = None,
    ses: Optional[str] = None,
    search_str: str = "*",
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[Union[List[str], List[Path]], List[str]]:
    """Search project folder at the subject or session level.

    Parameters
    ----------
    cfg
        datashuttle project cfg. Currently, this is used
        as a holder for  ssh configs to avoid too many
        arguments, but this is not nice and breaks the
        general rule that these functions should operate
        project-agnostic.

    base_folder
        the path to the base folder. If sub is None, the search is
        performed on this folder

    local_or_central
        search in local or central project

    sub
        either a subject name (string) or None. If None, the search
        is performed at the base_folder level

    ses
        either a session name (string) or None, This must not
        be a session name if sub is None. If provided (with sub)
        then the session folder is searched

    search_str
        glob-format search string to search at the
        folder level.

    verbose
        If `True`, if a search folder cannot be found, a message
        will be printed with the un-found path.

    return_full_path
        include the search_path in the returned paths

    Returns
    -------
    Discovered folders (`all_folder_names`) and files (`all_filenames`).

    """
    if ses and not sub:
        utils.log_and_raise_error(
            "cannot pass session to search_sub_or_ses_level() without subject",
            ValueError,
        )

    if sub:
        base_folder = base_folder / sub

    if ses:
        base_folder = base_folder / ses

    all_folder_names, all_filenames = search_for_folders(
        cfg,
        base_folder,
        local_or_central,
        search_str,
        verbose,
        return_full_path,
    )

    return all_folder_names, all_filenames


def search_for_folders(
    cfg: Configs,
    search_path: Path,
    local_or_central: str,
    search_prefix: str,
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[List[Any], List[Any]]:
    """Search for files and folders in the search path.

    If searching the local filesystem, use a separate function that does not call `rclone`,
    which is faster as a new process does not have to be created. This slowness
    is mostly a problem on Windows. This does mean there are two duplicate functions,
    these are tested against each-other in unit tests.

    Parameters
    ----------
    cfg
        datashuttle configs

    local_or_central
        "local" or "central"

    search_path
        full filepath to search in

    search_prefix
        file / folder name to search (e.g. "sub-*")

    verbose
        If `True`, when a search folder cannot be found, a message
        will be printed with the missing path.

    return_full_path
        include the search_path in the returned paths

    Returns
    -------
    Discovered folders (`all_folder_names`) and files (`all_filenames`).

    """
    if (
        local_or_central == "local"
        or cfg["connection_method"] == "local_filesystem"
    ):
        if not search_path.exists():
            if verbose:
                utils.log_and_message(
                    f"No file found at {search_path.as_posix()}"
                )
            return [], []

        all_folder_names, all_filenames = search_local_filesystem(
            search_path, search_prefix, return_full_path
        )

    else:
        all_folder_names, all_filenames = search_central_via_connection(
            cfg,
            search_path,
            search_prefix,
            return_full_path,
        )

    return all_folder_names, all_filenames


def search_local_filesystem(
    search_path: Path, search_prefix: str, return_full_path: bool = False
) -> tuple[List[Any], List[Any]]:
    """Search local filesystem recursively.

    Partner function to `search_central_via_connection()` for use
    locally as is much faster than calling `rclone` through a new process.

    Parameters
    ----------
    search_path
        The path to search (relative to the local or remote drive). For example,
        for "local_filesystem" this is the path on the local machine. For any other
        connection to central, this is the path on the central storage that has been
        connected to.

    search_prefix
        The search string e.g. "sub-*".

    return_full_path
        If `True`, return the full filepath, otherwise return only the folder/file name.

    """
    all_folder_names = []
    all_filenames = []

    for item in search_path.glob(search_prefix):
        to_append = item if return_full_path else item.name

        if item.is_dir():
            all_folder_names.append(to_append)
        elif item.is_file():
            all_filenames.append(to_append)

    return sorted(all_folder_names), sorted(all_filenames)


def search_central_via_connection(
    cfg: Configs,
    search_path: Path,
    search_prefix: str,
    return_full_path: bool = False,
) -> tuple[List[Any], List[Any]]:
    """Search for files and folders in central path using `rclone lsjson` command.

    This command lists all the files and folders in the central path in a json format.
    The json contains file/folder info about each file/folder like name, type, etc.

    Parameters
    ----------
    cfg
        datashuttle Configs class.
    search_path
        The path to search (relative to the local or remote drive). For example,
        for "local_filesystem" this is the path on the local machine. For any other
        connection to central, this is the path on the central storage that has been
        connected to.

    search_prefix
        The search string e.g. "sub-*".

    return_full_path
        If `True`, return the full filepath, otherwise return only the folder/file name.

    """
    rclone_config_name = cfg.get_rclone_config_name(cfg["connection_method"])

    output = rclone.call_rclone(
        f'lsjson {rclone_config_name}:"{search_path.as_posix()}"',
        pipe_std=True,
    )

    all_folder_names: list = []
    all_filenames: list = []

    if output.returncode != 0:
        utils.log_and_message(
            f"Error searching files at {search_path.as_posix()}\n"
            f"{output.stderr.decode('utf-8') if output.stderr else ''}"
        )
        return all_folder_names, all_filenames

    files_and_folders = json.loads(output.stdout)

    for file_or_folder in files_and_folders:
        name = file_or_folder["Name"]

        if not fnmatch.fnmatch(name, search_prefix):
            continue

        is_dir = file_or_folder.get("IsDir", False)

        to_append = search_path / name if return_full_path else name

        if is_dir:
            all_folder_names.append(to_append)
        else:
            all_filenames.append(to_append)

    return sorted(all_folder_names), sorted(all_filenames)
