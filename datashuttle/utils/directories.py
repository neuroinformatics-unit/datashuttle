import glob
import os
import warnings
from pathlib import Path
from typing import List, Union

from . import ssh

# --------------------------------------------------------------------------------------------------------------------
# Directory Utils
# --------------------------------------------------------------------------------------------------------------------


def make_dirs(paths: Union[Path, List[Path]]) -> None:
    """
    For path or list of path, make them if
    they do not already exist.
    """
    if isinstance(paths, Path):
        paths = [paths]

    for path_ in paths:

        if not path_.is_dir():
            path_.mkdir(parents=True)
        else:
            warnings.warn(
                "The following directory was not made "
                "because it already exists"
                f" {path_.as_posix()}"
            )


def make_datashuttle_metadata_folder(full_path: Path) -> None:
    meta_folder_path = full_path / ".datashuttle_meta"
    make_dirs(meta_folder_path)


def search_filesystem_path_for_directories(
    search_path_with_prefix: Path,
) -> List[str]:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning directories only.
    """
    all_dirnames = []
    for file_or_dir in glob.glob(search_path_with_prefix.as_posix()):
        if os.path.isdir(file_or_dir):
            all_dirnames.append(os.path.basename(file_or_dir))
    return all_dirnames


def process_glob_to_find_data_type_dirs(
    directory_names: list,
    data_type_dirs: dict,
) -> zip:
    """
    Process the results of glob on a sub or session level,
    which could contain any kind of folder / file.
    Find the data_type files and return in
    a format that mirros dict.items()
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


def search_for_directories(
    project, local_or_remote: str, search_path: Path, search_prefix: str
) -> List[str]:
    """
    Wrapper to determine the method used to search for search
    prefix directories in the search path.

    :param local_or_remote: "local" or "remote"
    :param search_path: full filepath to search in
    :param search_prefix: file / dirname to search (e.g. "sub-*")
    """
    if (
        local_or_remote == "remote"
        and project.cfg["connection_method"] == "ssh"
    ):

        all_dirnames = ssh.search_ssh_remote_for_directories(
            search_path,
            search_prefix,
            project.cfg,
            project._hostkeys,
            project._ssh_key_path,
        )
    else:
        all_dirnames = search_filesystem_path_for_directories(
            search_path / search_prefix
        )
    return all_dirnames
