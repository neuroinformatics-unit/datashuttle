from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datashuttle.datashuttle import DataShuttle
    from datashuttle.configs.config_class import Configs

import glob
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from datashuttle.configs.canonical_tags import tags

from . import formatting, ssh, utils

# --------------------------------------------------------------------------------------------------------------------
# Make Folders
# --------------------------------------------------------------------------------------------------------------------


def make_folder_trees(
    cfg: Configs,
    sub_names: Union[str, list],
    ses_names: Union[str, list],
    data_type: str,
    log: bool = True,
) -> None:
    """
    Entry method to make a full folder tree. It will
    iterate through all passed subjects, then sessions, then
    subfolders within a data_type folder. This
    permits flexible creation of folders (e.g.
    to make subject only, do not pass session name.

    Ensure sub and ses names are already formatted
    before use in this function (see _start_log())

    Parameters
    ----------

    sub_names, ses_names, data_type : see make_sub_folders()

    log : whether to log or not. If True, logging must
        already be initialised.
    """
    data_type_passed = data_type not in [[""], ""]

    if data_type_passed:
        formatting.check_data_type_is_valid(cfg, data_type, error_on_fail=True)

    for sub in sub_names:

        sub_path = cfg.make_path(
            "local",
            sub,
        )

        make_folders(sub_path, log)

        if data_type_passed:
            make_data_type_folders(cfg, data_type, sub_path, "sub")

        for ses in ses_names:

            ses_path = cfg.make_path(
                "local",
                [sub, ses],
            )

            make_folders(ses_path, log)

            if data_type_passed:
                make_data_type_folders(
                    cfg, data_type, ses_path, "ses", log=log
                )


def make_data_type_folders(
    cfg: Configs,
    data_type: Union[list, str],
    sub_or_ses_level_path: Path,
    level: str,
    log: bool = True,
) -> None:
    """
    Make data_type folder (e.g. behav) at the sub or ses
    level. Checks folder_class.Folders attributes,
    whether the data_type is used and at the current level.

    Parameters
    ----------
    data_type : data type (e.g. "behav", "all") to use. Use
        empty string ("") for none.

    sub_or_ses_level_path : Full path to the subject
        or session folder where the new folder
        will be written.

    level : The folder level that the
        folder will be made at, "sub" or "ses"

    log : whether to log on or not (if True, logging must
        already be initialised).
    """
    data_type_items = cfg.get_data_type_items(data_type)

    for data_type_key, data_type_folder in data_type_items:  # type: ignore

        if data_type_folder.used and data_type_folder.level == level:
            data_type_path = sub_or_ses_level_path / data_type_folder.name

            make_folders(data_type_path, log)

            make_datashuttle_metadata_folder(data_type_path, log)


# Make Folderes Helpers ----------------------------------------------------------------


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


def make_datashuttle_metadata_folder(
    full_path: Path, log: bool = True
) -> None:
    """
    Make a .datashuttle folder (this is created
    in the local_path for logs and User folder
    for configs). See make_folders() for arguments.
    """
    meta_folder_path = full_path / ".datashuttle_meta"
    make_folders(meta_folder_path, log)


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
    if new_ses_names is None:
        existing_sub_names = search_sub_or_ses_level(
            project.cfg, base_folder, "local"
        )[0]
        existing_sub_values = utils.get_first_sub_ses_keys(existing_sub_names)

        for new_sub in utils.get_first_sub_ses_keys(new_sub_names):
            if new_sub in existing_sub_values:
                utils.log_and_raise_error(
                    f"Cannot make folders. "
                    f"The key sub-{new_sub} already exists in the project"
                )
    else:
        # for each subject, check session level
        for sub in new_sub_names:
            existing_ses_names = search_sub_or_ses_level(
                project.cfg, base_folder, "local", sub
            )[0]

            existing_ses_values = utils.get_first_sub_ses_keys(
                existing_ses_names
            )

            for new_ses in utils.get_first_sub_ses_keys(new_ses_names):

                if new_ses in existing_ses_values:
                    utils.log_and_raise_error(
                        f"Cannot make folders. "
                        f"The key ses-{new_ses} for {sub} already exists in the project"
                    )


# --------------------------------------------------------------------
# Search Existing Folderes
# --------------------------------------------------------------------

# Search Subjects / Sessions
# --------------------------------------------------------------------


def search_sub_or_ses_level(
    cfg: Configs,
    base_folder: Path,
    local_or_remote: str,
    sub: Optional[str] = None,
    ses: Optional[str] = None,
    search_str: str = "*",
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

    local_or_remote : search in local or remote project

    sub : either a subject name (string) or None. If None, the search
        is performed at the top_level_folder_name level

    ses: either a session name (string) or None, This must not
        be a session name if sub is None. If provided (with sub)
        then the session folder is searched

    str: glob-format search string to search at the
        folder level.
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
        cfg, base_folder, local_or_remote, search_str
    )

    return all_folder_names, all_filenames


def search_data_folders_sub_or_ses_level(
    cfg: Configs,
    base_folder: Path,
    local_or_remote: str,
    sub: str,
    ses: Optional[str] = None,
) -> zip:
    """
    Search  a subject or session folder specifically
    for data_types. First searches for all folders / files
    in the folder, and then returns any folders that
    match data_type name.

    see folders.search_sub_or_ses_level() for full
    parameters list.

    Returns
    -------
    Find the data_type files and return in
    a format that mirrors dict.items()
    """
    search_results = search_sub_or_ses_level(
        cfg, base_folder, local_or_remote, sub, ses
    )[0]

    data_folders = process_glob_to_find_data_type_folders(
        search_results,
        cfg.data_type_folders,
    )

    return data_folders


def search_for_wildcards(
    cfg: Configs,
    base_folder: Path,
    local_or_remote: str,
    all_names: List[str],
    sub: Optional[str] = None,
) -> List[str]:
    """
    Handle wildcard flag in upload_data or download_data.

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

    local_or_remote : "local" or "remote" project path to
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
        if tags("*") in name:
            name = name.replace(tags("*"), "*")

            if sub:
                matching_names = search_sub_or_ses_level(
                    cfg, base_folder, local_or_remote, sub, search_str=name
                )[0]
            else:
                matching_names = search_sub_or_ses_level(
                    cfg, base_folder, local_or_remote, search_str=name
                )[0]

            new_all_names += matching_names
        else:
            new_all_names += [name]

    new_all_names = list(
        set(new_all_names)
    )  # remove duplicate names in case of wildcard overlap

    return new_all_names


# Search Data Types
# --------------------------------------------------------------------


def process_glob_to_find_data_type_folders(
    folder_names: list,
    data_type_folders: dict,
) -> zip:
    """
    Process the results of glob on a sub or session level,
    which could contain any kind of folder / file.

    see project.search_sub_or_ses_level() for inputs.

    Returns
    -------
    Find the data_type files and return in
    a format that mirrors dict.items()
    """
    ses_folder_keys = []
    ses_folder_values = []
    for name in folder_names:
        data_type_key = [
            key
            for key, value in data_type_folders.items()
            if value.name == name
        ]

        if data_type_key:
            ses_folder_keys.append(data_type_key[0])
            ses_folder_values.append(data_type_folders[data_type_key[0]])

    return zip(ses_folder_keys, ses_folder_values)


# Low level search functions
# --------------------------------------------------------------------


def search_for_folders(  # TODO: change name
    cfg: Configs,
    search_path: Path,
    local_or_remote: str,
    search_prefix: str,
) -> Tuple[List[Any], List[Any]]:
    """
    Wrapper to determine the method used to search for search
    prefix folders in the search path.

    Parameters
    ----------

    local_or_remote : "local" or "remote"
    search_path : full filepath to search in
    search_prefix : file / folder name to search (e.g. "sub-*")
    """
    if local_or_remote == "remote" and cfg["connection_method"] == "ssh":

        all_folder_names, all_filenames = ssh.search_ssh_remote_for_folders(
            search_path,
            search_prefix,
            cfg,
        )
    else:

        if not search_path.exists():
            utils.log_and_message(f"No file found at {search_path.as_posix()}")
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
