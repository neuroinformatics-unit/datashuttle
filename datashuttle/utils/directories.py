import glob
import os
import warnings
from pathlib import Path
from typing import Union

# --------------------------------------------------------------------------------------------------------------------
# Directory Utils
# --------------------------------------------------------------------------------------------------------------------


def make_dirs(paths: Union[Path, list[Path]]) -> None:
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
) -> list[str]:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning directories only.
    """
    all_dirnames = []
    for file_or_dir in glob.glob(search_path_with_prefix.as_posix()):
        if os.path.isdir(file_or_dir):
            all_dirnames.append(os.path.basename(file_or_dir))
    return all_dirnames
