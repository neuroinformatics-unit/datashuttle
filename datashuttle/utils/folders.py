from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs

import glob
import os
import warnings
from collections.abc import ItemsView
from pathlib import Path



from .custom_exceptions import NeuroBlueprintError
from datashuttle.configs import canonical_folders, canonical_tags
from . import folders, ssh, utils, validation


# -----------------------------------------------------------------------------
# Make Folders
# -----------------------------------------------------------------------------


def make_folder_trees(
    cfg: Configs,
    sub_names: Union[str, list],
    ses_names: Union[str, list],
    datatype: Union[List[str], str],
    log: bool = True,
) -> None:
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

    sub_names, ses_names, datatype : see make_folders()

    log : whether to log or not. If True, logging must
        already be initialised.
    """
    datatype_passed = datatype not in [[""], ""]

    if datatype_passed:
        validation.check_datatype_is_valid(
            datatype, error_on_fail=True, allow_all=True
        )

    for sub in sub_names:
        sub_path = cfg.make_path(
            "local",
            sub,
        )

        make_folders(sub_path, log)

        if datatype_passed:
            make_datatype_folders(cfg, datatype, sub_path, "sub")

        for ses in ses_names:
            ses_path = cfg.make_path(
                "local",
                [sub, ses],
            )

            make_folders(ses_path, log)

            if datatype_passed:
                make_datatype_folders(cfg, datatype, ses_path, "ses", log=log)


def make_datatype_folders(
    cfg: Configs,
    datatype: Union[list, str],
    sub_or_ses_level_path: Path,
    level: str,
    log: bool = True,
) -> None:
    """
    Make datatype folder (e.g. behav) at the sub or ses
    level. Checks folder_class.Folders attributes,
    whether the datatype is used and at the current level.

    Parameters
    ----------
    datatype : datatype (e.g. "behav", "all") to use. Use
        empty string ("") for none.

    sub_or_ses_level_path : Full path to the subject
        or session folder where the new folder
        will be written.

    level : The folder level that the
        folder will be made at, "sub" or "ses"

    log : whether to log on or not (if True, logging must
        already be initialised).
    """
    datatype_items = cfg.get_datatype_items(datatype)

    for datatype_key, datatype_folder in datatype_items:  # type: ignore
        if datatype_folder.level == level:
            datatype_path = sub_or_ses_level_path / datatype_folder.name

            make_folders(datatype_path, log)


# Make Folders Helpers --------------------------------------------------------


def make_folders(paths: Union[Path, List[Path]], log: bool = True) -> None:
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


def get_all_sub_and_ses_names(
    cfg: Configs,
) -> Dict:
    """
    Get a list of every subject and session name in the
    local and central project folders. Local and central names are combined
    into a single list, separately for subject and sessions.

    Note this only finds local sub and ses names on this
    machine. Other local machines are not searched.
    """
    sub_folder_names = get_local_and_central_sub_or_ses_names(
        cfg, None, "sub-*"
    )

    all_sub_folder_names = (
        sub_folder_names["local"] + sub_folder_names["central"]
    )

    all_ses_folder_names = []
    for sub in all_sub_folder_names:
        ses_folder_names = get_local_and_central_sub_or_ses_names(
            cfg, sub, "ses-*"
        )

        all_ses_folder_names.extend(
            ses_folder_names["local"] + ses_folder_names["central"]
        )

    return {"sub": all_sub_folder_names, "ses": all_ses_folder_names}


def get_local_and_central_sub_or_ses_names(
    cfg: Configs, sub: Optional[str], search_str: str
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
        cfg.get_base_folder("local"),
        "local",
        sub=sub,
        search_str=search_str,
        verbose=False,
    )
    central_foldernames, _ = search_sub_or_ses_level(
        cfg,
        cfg.get_base_folder("central"),
        "central",
        sub,
        search_str=search_str,
        verbose=False,
    )
    return {"local": local_foldernames, "central": central_foldernames}


# Search Data Types
# -----------------------------------------------------------------------------


def items_from_datatype_input(
    cfg: Configs,
    local_or_central: str,
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
    base_folder = cfg.get_base_folder(local_or_central)

    if datatype not in [
        "all",
        ["all"],
        "all_datatype",
        ["all_datatype"],
    ]:
        datatype_items = cfg.get_datatype_items(
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


def search_for_wildcards(
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
    new_all_names = []
    for name in all_names:
        if canonical_tags.tags("*") in name:
            name = name.replace(canonical_tags.tags("*"), "*")

            if sub:
                matching_names = search_sub_or_ses_level(
                    cfg, base_folder, local_or_central, sub, search_str=name
                )[0]
            else:
                matching_names = search_sub_or_ses_level(
                    cfg, base_folder, local_or_central, search_str=name
                )[0]

            new_all_names += matching_names
        else:
            new_all_names += [name]

    new_all_names = list(
        set(new_all_names)
    )  # remove duplicate names in case of wildcard overlap

    return new_all_names


# -----------------------------------------------------------------------------
# Low level search functions
# -----------------------------------------------------------------------------


def search_sub_or_ses_level(
    cfg: Configs,
    base_folder: Path,
    local_or_central: str,
    sub: Optional[str] = None,
    ses: Optional[str] = None,
    search_str: str = "*",
    verbose: bool = True,
) -> Tuple[List[str], List[str]]:
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
            "search_sub_or_ses_level() without subject"
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
    )

    return all_folder_names, all_filenames


def search_for_folders(
    cfg: Configs,
    search_path: Path,
    local_or_central: str,
    search_prefix: str,
    verbose: bool = True,
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
        )
    else:
        if not search_path.exists():
            if verbose:
                utils.log_and_message(
                    f"No file found at {search_path.as_posix()}"
                )
            return [], []

        all_folder_names, all_filenames = search_filesystem_path_for_folders(
            search_path / search_prefix
        )
    return all_folder_names, all_filenames


def search_filesystem_path_for_folders(
    search_path_with_prefix: Path,
) -> Tuple[List[str], List[str]]:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning folders only.
    """
    all_folder_names = []
    all_filenames = []
    for file_or_folder in glob.glob(search_path_with_prefix.as_posix()):
        if os.path.isdir(file_or_folder):
            all_folder_names.append(os.path.basename(file_or_folder))
        else:
            all_filenames.append(os.path.basename(file_or_folder))

    return all_folder_names, all_filenames


# -----------------------------------------------------------------------------
# Project Getters (TODO: own module)
# -----------------------------------------------------------------------------


def get_next_sub_or_ses_number(
    cfg: Configs,
    sub: Optional[str],
    search_str: str,
    return_with_prefix: bool = True,
    default_num_value_digits: int = 3,
) -> str:
    """
    Suggest the next available subject or session number. This function will
    search the local repository, and the central repository, for all subject
    or session folders (subject or session depending on inputs).

    It will take the union of all folder names, find the relevant key-value
    pair values, and return the maximum value + 1 as the new number.

    A warning will be shown if the existing sub / session numbers are not
    consecutive.

    Parameters
    ----------
    cfg : Configs
        datashuttle configs class

    sub : Optional[str]
        subject name to search within if searching for sessions, otherwise None
        to search for subjects

    search_str : str
        the string to search for within the top-level or subject-level
        folder ("sub-*") or ("ses-*") are suggested, respectively.

    return_with_prefix : bool
        If `True`, the next sub or ses value will include the prefix
        e.g. "sub-001", otherwise the value alone will be returned (e.g. "001")

    default_num_value_digits : int
        If no sub or ses exist in the project, the starting number is 1.
        Because the number of digits for the project is not accessible,
        the desired value can be entered here. e.g. if 3 (the default),
        if no subjects are found the subject returned will be "sub-001".

    Returns
    -------
    suggested_new_num : the new suggested sub / ses.
    """
    prefix: Literal["sub", "ses"]

    if sub:
        prefix = "ses"
    else:
        prefix = "sub"

    folder_names = get_local_and_central_sub_or_ses_names(
        cfg,
        sub,
        search_str,
    )

    all_folders = list(set(folder_names["local"] + folder_names["central"]))

    (
        max_existing_num,
        num_value_digits,
    ) = get_max_sub_or_ses_num_and_value_length(
        all_folders, prefix, default_num_value_digits
    )

    # calculate next sub number
    suggested_new_num = max_existing_num + 1
    format_suggested_new_num = str(suggested_new_num).zfill(num_value_digits)

    if return_with_prefix:
        format_suggested_new_num = f"{prefix}-{format_suggested_new_num}"

    return format_suggested_new_num


def get_max_sub_or_ses_num_and_value_length(
    all_folders: List[str],
    prefix: Literal["sub", "ses"],
    default_num_value_digits: Optional[int] = None,
) -> Tuple[int, int]:
    """
    Given a list of BIDS-style folder names, find the maximum subject or
    session value (sub or ses depending on `prefix`). Also, find the
    number of value digits across the project, so a new suggested number
    can be formatted consistency. If the list is empty, set the value
    to 0 and a default number of value digits.

    Parameters
    ----------

    all_folders : List[str]
        A list of BIDS-style formatted folder names.

    see `get_next_sub_or_ses_number()` for other arguments.

    Returns
    -------

    max_existing_num : int
        The largest number sub / ses value in the past list.

    num_value_digits : int
        The length of the value in all sub / ses values within the
        passed list. If these are not consistent, an error is raised.

    For example, if the project contains "sub-0001", "sub-0002" then
    the max_existing_num will be 2 and num_value_digits 4.

    """
    if len(all_folders) == 0:
        max_existing_num = 0
        assert isinstance(
            default_num_value_digits, int
        ), "`default_num_value_digits` must be int`"

        num_value_digits = default_num_value_digits
    else:
        all_values_str = utils.get_values_from_bids_formatted_name(
            all_folders,
            prefix,
            return_as_int=False,
        )

        # First get the length of bids-key value across the project
        # (e.g. sub-003 has three values).
        all_num_value_digits = [len(value) for value in all_values_str]

        if not len(set(all_num_value_digits)) == 1:
            utils.raise_error(
                f"The number of value digits for the {prefix} level are not "
                f"consistent. Cannot suggest a {prefix} number.",
                NeuroBlueprintError,
            )
        num_value_digits = all_num_value_digits[0]

        # Then get the latest existing sub or ses number in the project.
        all_value_nums = sorted(
            [utils.sub_or_ses_value_to_int(value) for value in all_values_str]
        )

        if not utils.integers_are_consecutive(all_value_nums):
            warnings.warn(
                f"A subject number has been skipped, "
                f"currently used subject numbers are: {all_value_nums}"
            )

        max_existing_num = max(all_value_nums)

    return max_existing_num, num_value_digits


def get_existing_project_paths_and_names() -> Tuple[List[str], List[Path]]:
    """
    Return full path and names of datashuttle projects on
    this local machine. A project is determined by a project
    folder in the home / .datashuttle folder that contains a
    config.yaml file.
    """
    datashuttle_path = canonical_folders.get_datashuttle_path()

    all_folders, _ = folders.search_filesystem_path_for_folders(
        datashuttle_path / "*"
    )

    existing_project_paths = []
    existing_project_names = []
    for folder_name in all_folders:
        config_file = list(
            (datashuttle_path / folder_name).glob("config.yaml")
        )

        if len(config_file) > 1:
            utils.raise_error(
                f"There are two config files in project"
                f"{folder_name} at path {datashuttle_path}. There "
                f"should only ever be one config per project. ",
                NeuroBlueprintError,
            )
        elif len(config_file) == 1:
            existing_project_paths.append(datashuttle_path / folder_name)
            existing_project_names.append(folder_name)

    return existing_project_names, existing_project_paths
