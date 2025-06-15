from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

if TYPE_CHECKING:
    from collections.abc import ItemsView

    from datashuttle.configs.config_class import Configs
    from datashuttle.utils.custom_types import TopLevelFolder

import glob
import re
from datetime import datetime
from pathlib import Path

from datashuttle.configs import canonical_folders, canonical_tags
from datashuttle.utils import ssh, utils, validation
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
    """
    Entry method to make a full folder tree. It will
    iterate through all passed subjects, then sessions, then
    subfolders within a datatype folder. This
    permits flexible creation of folders (e.g.
    to make subject only, do not pass session name.

    Ensure sub and ses names are already formatted
    before use in this function (see _start_log())

    Parameters
    ----------

    sub_names, ses_names, datatype : see create_folders()

    log : whether to log or not. If True, logging must
        already be initialised.
    """
    datatype_passed = datatype not in [[""], ""]

    if "all" in datatype or datatype == "all":
        raise ValueError(
            "Using 'all' keyboard for `create_folders` "
            "datatype is deprecated in 0.6.0"
        )

    if datatype_passed:
        error_message = validation.check_datatypes_are_valid(
            datatype, allow_all=True
        )
        if error_message:
            utils.log_and_raise_error(error_message, NeuroBlueprintError)

        all_paths: Dict = {}
    else:
        all_paths = {
            "sub": [],
            "ses": [],
        }

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
    """
    Make datatype folder (e.g. behav) at the sub or ses
    level. Checks folder_class.Folders attributes,
    whether the datatype is used and at the current level.

    Parameters
    ----------
    cfg : ConfigsClass

    datatype : datatype (e.g. "behav", "all") to use. Use
        empty string ("") for none.

    sub_or_ses_level_path : Full path to the subject
        or session folder where the new folder
        will be written.

    level : The folder level that the
        folder will be made at, "sub" or "ses"

    save_paths : A dictionary, which will be filled
        with created paths split by datatype name.

    log : whether to log on or not (if True, logging must
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
    """
    For path or list of paths, make them if
    they do not already exist.

    Parameters
    ----------

    paths : Path or list of Paths to create

    log : if True, log all made folders. This
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
    """
    If sub is None, the top-level level folder will be
    searched (i.e. for subjects). The search string "sub-*" is suggested
    in this case. Otherwise, the subject, level folder for the specified
    subject will be searched. The search_str "ses-*" is suggested in this case.

    Note `verbose` argument of `search_sub_or_ses_level()` is set to `False`,
    as session folders for local subjects that are not yet on central
    will be searched for on central, showing a confusing 'folder not found'
    message.
    """

    # Search local and central for folders that begin with "sub-*"
    local_foldernames, _ = search_sub_or_ses_level(
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
        central_foldernames, _ = search_sub_or_ses_level(
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
    """
    Get the list of datatypes to transfer, either
    directly from user input, or by searching
    what is available if "all" is passed.

    Parameters
    ----------

    see _transfer_datatype() for parameters.
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
    """
    Search a subject or session folder specifically
    for datatypes. First searches for all folders / files
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
    """
    Process the results of glob on a sub or session level,
    which could contain any kind of folder / file.

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


# Wildcards
# -----------------------------------------------------------------------------


def filter_names_by_datetime_range(
    names: List[str],
    format_type: str,
    start_timepoint: datetime,
    end_timepoint: datetime,
) -> List[str]:
    """
    Filter a list of names based on a datetime range.
    Assumes all names contain the format_type pattern (e.g., date-*, time-*)
    as they were searched using this pattern.

    Parameters
    ----------
    names : List[str]
        List of names to filter, all containing the datetime pattern
    format_type : str
        One of "datetime", "time", or "date"
    start_timepoint : datetime
        Start of the datetime range
    end_timepoint : datetime
        End of the datetime range

    Returns
    -------
    List[str]
        Filtered list of names that fall within the datetime range
    """
    filtered_names: List[str] = []
    for candidate in names:
        candidate_basename = candidate if isinstance(candidate, str) else candidate.name
        value = get_values_from_bids_formatted_name([candidate_basename], format_type)[0]
        try:
            candidate_timepoint = datetime.strptime(
                value, canonical_tags.get_datetime_format(format_type)
            )
            if start_timepoint <= candidate_timepoint <= end_timepoint:
                filtered_names.append(candidate)
        except ValueError:
            continue
    return filtered_names


def search_with_tags(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    all_names: List[str],
    sub: Optional[str] = None,
) -> List[str]:
    """
    Handle wildcard flag in upload or download.

    All names in name are searched for @*@ string, and replaced
    with single * for glob syntax. If sub is passed, it is
    assumes all_names is ses_names and the sub folder is searched
    for ses_names matching the name including wildcard. Otherwise,
    if sub is None it is assumed all_names are sub names and
    the level above is searched.

    Outputs a new list of names including all original names
    but where @*@-containing names have been replaced with
    search results.

    Parameters
    ----------

    project : initialised datashuttle project

    base_folder : folder to search for wildcards in

    local_or_central : "local" or "central" project path to
        search in

    all_names : list of subject or session names that
        may or may not include the wildcard flag. If sub (below)
        is passed, it is assumed these are session names. Otherwise,
        it is assumed these are subject names.

    sub : optional subject to search for sessions in. If not provided,
        will search for subjects rather than sessions.
    """
    new_all_names: List[str] = []
    for name in all_names:
        if not (canonical_tags.tags("*") in name or
                canonical_tags.tags("DATETO") in name or
                canonical_tags.tags("TIMETO") in name or
                canonical_tags.tags("DATETIMETO") in name):
            new_all_names.append(name)
            continue

        # Initialize search string
        search_str = name

        # Handle wildcard replacement first if present
        if canonical_tags.tags("*") in name:
            search_str = search_str.replace(canonical_tags.tags("*"), "*")

        # Handle datetime ranges
        format_type = tag = None
        if canonical_tags.tags("DATETO") in search_str:
            format_type = "date"
            tag = canonical_tags.tags("DATETO")
        elif canonical_tags.tags("TIMETO") in search_str:
            format_type = "time"
            tag = canonical_tags.tags("TIMETO")
        elif canonical_tags.tags("DATETIMETO") in search_str:
            format_type = "datetime"
            tag = canonical_tags.tags("DATETIMETO")

        if format_type is not None:
            assert tag is not None, "format and tag should be set together"
            search_str = validation.format_and_validate_datetime_search_str(search_str, format_type, tag)

        # Use the helper function to perform the glob search
        if sub:
            matching_names: List[str] = search_sub_or_ses_level(
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

        # Filter results by datetime range if one was present
        if format_type is not None and tag is not None:
            expected_values = validation.get_expected_num_datetime_values(format_type)
            full_tag_regex = fr"(\d{{{expected_values}}}){re.escape(tag)}(\d{{{expected_values}}})"
            match = re.search(full_tag_regex, name)
            if match:  # We know this is true because format_and_validate_datetime_search_str succeeded
                start_str, end_str = match.groups()
                start_timepoint = datetime.strptime(start_str, canonical_tags.get_datetime_format(format_type))
                end_timepoint = datetime.strptime(end_str, canonical_tags.get_datetime_format(format_type))
                matching_names = filter_names_by_datetime_range(
                    matching_names, format_type, start_timepoint, end_timepoint
                )

        new_all_names.extend(matching_names)

    # Remove duplicates in case of wildcard overlap
    new_all_names = list(set(new_all_names))
    return new_all_names


# -----------------------------------------------------------------------------
# Low level search functions
# -----------------------------------------------------------------------------


# @overload: Cannot get type overloading to work with this function.
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
    """
    Search project folder at the subject or session level.
    Only returns folders

    Parameters
    ----------

    cfg : datashuttle project cfg. Currently, this is used
        as a holder for  ssh configs to avoid too many
        arguments, but this is not nice and breaks the
        general rule that these functions should operate
        project-agnostic.

    local_or_central : search in local or central project

    sub : either a subject name (string) or None. If None, the search
        is performed at the top_level_folder level

    ses : either a session name (string) or None, This must not
        be a session name if sub is None. If provided (with sub)
        then the session folder is searched

    str : glob-format search string to search at the
        folder level.

    verbose : If `True`, if a search folder cannot be found, a message
              will be printed with the un-found path.
    """
    if ses and not sub:
        utils.log_and_raise_error(
            "cannot pass session to "
            "search_sub_or_ses_level() without subject",
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
    """
    Wrapper to determine the method used to search for search
    prefix folders in the search path.

    Parameters
    ----------

    local_or_central : "local" or "central"
    search_path : full filepath to search in
    search_prefix : file / folder name to search (e.g. "sub-*")
    verbose : If `True`, when a search folder cannot be found, a message
          will be printed with the missing path.
    """
    if local_or_central == "central" and cfg["connection_method"] == "ssh":
        all_folder_names, all_filenames = ssh.search_ssh_central_for_folders(
            search_path,
            search_prefix,
            cfg,
            verbose,
            return_full_path,
        )
    else:
        if not search_path.exists():
            if verbose:
                utils.log_and_message(
                    f"No file found at {search_path.as_posix()}"
                )
            return [], []

        all_folder_names, all_filenames = search_filesystem_path_for_folders(
            search_path / search_prefix, return_full_path
        )
    return all_folder_names, all_filenames


# Actual function implementation
def search_filesystem_path_for_folders(
    search_path_with_prefix: Path, return_full_path: bool = False
) -> Tuple[List[Path | str], List[Path | str]]:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning folders only.
    """
    all_folder_names = []
    all_filenames = []

    all_files_and_folders = list(glob.glob(search_path_with_prefix.as_posix()))
    sorter_files_and_folders = sorted(all_files_and_folders)

    for file_or_folder_str in sorter_files_and_folders:

        file_or_folder = Path(file_or_folder_str)

        if file_or_folder.is_dir():
            all_folder_names.append(
                file_or_folder if return_full_path else file_or_folder.name
            )
        else:
            all_filenames.append(
                file_or_folder if return_full_path else file_or_folder.name
            )

    return all_folder_names, all_filenames
