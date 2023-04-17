from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datashuttle.datashuttle import DataShuttle
    from datashuttle.configs.configs import Configs

import glob
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from datashuttle.configs.canonical_tags import tags

from . import formatting, ssh, utils

# --------------------------------------------------------------------------------------------------------------------
# Make Dirs
# --------------------------------------------------------------------------------------------------------------------


def make_directory_trees(
    cfg: Configs,
    sub_names: Union[str, list],
    ses_names: Union[str, list],
    data_type: str,
    log: bool = True,
) -> None:
    """
    Entry method to make a full directory tree. It will
    iterate through all passed subjects, then sessions, then
    subdirs within a data_type directory. This
    permits flexible creation of directories (e.g.
    to make subject only, do not pass session name.

    Ensure sub and ses names are already formatted
    before use in this function (see _start_log())

    Parameters
    ----------

    sub_names, ses_names, data_type : see make_sub_dir()

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

        make_dirs(sub_path, log)

        if data_type_passed:
            make_data_type_directories(cfg, data_type, sub_path, "sub")

        for ses in ses_names:

            ses_path = cfg.make_path(
                "local",
                [sub, ses],
            )

            make_dirs(ses_path, log)

            if data_type_passed:
                make_data_type_directories(
                    cfg, data_type, ses_path, "ses", log=log
                )


def make_data_type_directories(
    cfg: Configs,
    data_type: Union[list, str],
    sub_or_ses_level_path: Path,
    level: str,
    log: bool = True,
) -> None:
    """
    Make data_type folder (e.g. behav) at the sub or ses
    level. Checks directory_class.Directories attributes,
    whether the data_type is used and at the current level.

    Parameters
    ----------
    data_type : data type (e.g. "behav", "all") to use. Use
        empty string ("") for none.

    sub_or_ses_level_path : Full path to the subject
        or session directory where the new directory
        will be written.

    level : The directory level that the
        directory will be made at, "sub" or "ses"

    log : whether to log on or not (if True, logging must
        already be initialised).
    """
    data_type_items = cfg.get_data_type_items(data_type)

    for data_type_key, data_type_dir in data_type_items:  # type: ignore

        if data_type_dir.used and data_type_dir.level == level:
            data_type_path = sub_or_ses_level_path / data_type_dir.name

            make_dirs(data_type_path, log)

            make_datashuttle_metadata_folder(data_type_path, log)


# Make Dirs Helpers --------------------------------------------------------------------------------------------------


def make_dirs(paths: Union[Path, List[Path]], log: bool = True) -> None:
    """
    For path or list of paths, make them if
    they do not already exist.

    Parameters
    ----------

    paths : Path or list of Paths to create

    log : if True, log all made directories. This
        requires the logger to already be initialised.
    """
    if isinstance(paths, Path):
        paths = [paths]

    for path_ in paths:

        if not path_.is_dir():
            path_.mkdir(parents=True)
            if log:
                utils.log(f"Made directory at path: {path_}")


def make_datashuttle_metadata_folder(
    full_path: Path, log: bool = True
) -> None:
    """
    Make a .datashuttle folder (this is created
    in the local_path for logs and User directory
    for configs). See make_dirs() for arguments.
    """
    meta_folder_path = full_path / ".datashuttle_meta"
    make_dirs(meta_folder_path, log)


def check_no_duplicate_sub_ses_key_values(
    project: DataShuttle,
    base_dir: Path,
    new_sub_names: List[str],
    new_ses_names: Optional[List[str]] = None,
) -> None:
    """
    Given a list of subject and optional session names,
    check whether these already exist in the local project
    directory.

    This uses search_sub_or_ses_level() to search the local
    directory and then checks for the putative new subject
    or session names to determine any matches.

    Parameters
    ----------

    project : initialised datashuttle project

    base_dir : local_path to search

    new_sub_names : list of subject names that are being
     checked for duplicates

    new_ses_names : list of session names that are being
     checked for duplicates
    """
    if new_ses_names is None:
        existing_sub_names = search_sub_or_ses_level(
            project.cfg, base_dir, "local"
        )[0]
        existing_sub_values = utils.get_first_sub_ses_keys(existing_sub_names)

        for new_sub in utils.get_first_sub_ses_keys(new_sub_names):
            if new_sub in existing_sub_values:
                utils.log_and_raise_error(
                    f"Cannot make directories. "
                    f"The key sub-{new_sub} already exists in the project"
                )
    else:
        # for each subject, check session level
        for sub in new_sub_names:
            existing_ses_names = search_sub_or_ses_level(
                project.cfg, base_dir, "local", sub
            )[0]

            existing_ses_values = utils.get_first_sub_ses_keys(
                existing_ses_names
            )

            for new_ses in utils.get_first_sub_ses_keys(new_ses_names):

                if new_ses in existing_ses_values:
                    utils.log_and_raise_error(
                        f"Cannot make directories. "
                        f"The key ses-{new_ses} for {sub} already exists in the project"
                    )


# --------------------------------------------------------------------
# Search Existing Dirs
# --------------------------------------------------------------------

# Search Subjects / Sessions
# --------------------------------------------------------------------


def search_sub_or_ses_level(
    cfg: Configs,
    base_dir: Path,
    local_or_remote: str,
    sub: Optional[str] = None,
    ses: Optional[str] = None,
    search_str: str = "*",
) -> Tuple[List[str], List[str]]:
    """
    Search project folder at the subject or session level.
    Only returns directories

    Parameters
    ----------

    cfg : datashuttle project cfg. Currently, this is used
        as a holder for  ssh configs to avoid too many
        arguments, but this is not nice and breaks the
        general rule that these functions should operate
        project-agnostic.

    local_or_remote : search in local or remote project

    sub : either a subject name (string) or None. If None, the search
        is performed at the top_level_dir_name level

    ses: either a session name (string) or None, This must not
        be a session name if sub is None. If provided (with sub)
        then the session dir is searched

    str: glob-format search string to search at the
        directory level.
    """
    if ses and not sub:
        utils.log_and_raise_error(
            "cannot pass session to "
            "search_sub_or_ses_level() without subject"
        )

    if sub:
        base_dir = base_dir / sub

    if ses:
        base_dir = base_dir / ses

    all_dirnames, all_filenames = search_for_directories(
        cfg, base_dir, local_or_remote, search_str
    )

    return all_dirnames, all_filenames


def search_data_dirs_sub_or_ses_level(
    cfg: Configs,
    base_dir: Path,
    local_or_remote: str,
    sub: str,
    ses: Optional[str] = None,
) -> zip:
    """
    Search  a subject or session directory specifically
    for data_types. First searches for all folders / files
    in the directory, and then returns any dirs that
    match data_type name.

    see directories.search_sub_or_ses_level() for full
    parameters list.

    Returns
    -------
    Find the data_type files and return in
    a format that mirrors dict.items()
    """
    search_results = search_sub_or_ses_level(
        cfg, base_dir, local_or_remote, sub, ses
    )[0]

    data_directories = process_glob_to_find_data_type_dirs(
        search_results,
        cfg.data_type_dirs,
    )

    return data_directories


def search_for_wildcards(
    cfg: Configs,
    base_dir: Path,
    local_or_remote: str,
    all_names: List[str],
    sub: Optional[str] = None,
) -> List[str]:
    """
    Handle wildcard flag in upload_data or download_data.

    All names in name are searched for @*@ string, and replaced
    with single * for glob syntax. If sub is passed, it is
    assumes all_names is ses_names and the sub dir is searched
    for ses_names matching the name including wildcard. Otherwise,
    if sub is None it is assumed all_names are sub names and
    the level above is searched.

    Outputs a new list of names including all original names
    but where @*@-containing names have been replaced with
    search results.

    Parameters
    ----------

    project : initialised datashuttle project

    base_dir : directory to search for wildcards in

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
                    cfg, base_dir, local_or_remote, sub, search_str=name
                )[0]
            else:
                matching_names = search_sub_or_ses_level(
                    cfg, base_dir, local_or_remote, search_str=name
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


def process_glob_to_find_data_type_dirs(
    directory_names: list,
    data_type_dirs: dict,
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
    ses_dir_keys = []
    ses_dir_values = []
    for dir_name in directory_names:
        data_type_key = [
            key
            for key, value in data_type_dirs.items()
            if value.name == dir_name
        ]

        if data_type_key:
            ses_dir_keys.append(data_type_key[0])
            ses_dir_values.append(data_type_dirs[data_type_key[0]])

    return zip(ses_dir_keys, ses_dir_values)


# Low level search functions
# --------------------------------------------------------------------


def search_for_directories(  # TODO: change name
    cfg: Configs,
    search_path: Path,
    local_or_remote: str,
    search_prefix: str,
) -> Tuple[List[Any], List[Any]]:
    """
    Wrapper to determine the method used to search for search
    prefix directories in the search path.

    Parameters
    ----------

    local_or_remote : "local" or "remote"
    search_path : full filepath to search in
    search_prefix : file / dirname to search (e.g. "sub-*")
    """
    if local_or_remote == "remote" and cfg["connection_method"] == "ssh":

        all_dirnames, all_filenames = ssh.search_ssh_remote_for_directories(
            search_path,
            search_prefix,
            cfg,
        )
    else:

        if not search_path.exists():
            utils.log_and_message(f"No file found at {search_path.as_posix()}")
            return [], []

        all_dirnames, all_filenames = search_filesystem_path_for_directories(
            search_path / search_prefix
        )
    return all_dirnames, all_filenames


def search_filesystem_path_for_directories(
    search_path_with_prefix: Path,
) -> Tuple[List[str], List[str]]:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning directories only.
    """
    all_dirnames = []
    all_filenames = []
    for file_or_dir in glob.glob(search_path_with_prefix.as_posix()):
        if os.path.isdir(file_or_dir):
            all_dirnames.append(os.path.basename(file_or_dir))
        else:
            all_filenames.append(os.path.basename(file_or_dir))
    return all_dirnames, all_filenames
