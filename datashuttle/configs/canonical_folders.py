from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from datashuttle.utils.custom_types import TopLevelFolder

from datashuttle.configs import canonical_configs
from datashuttle.utils.folder_class import Folder


def get_datatype_folders() -> dict:
    """Return the canonical folders managed by datashuttle.

    Notes
    -----
    This organisation is somewhat legacy, and created to allow
    flexibility with the folder name vs. canonical name, and
    subject or session level. For now, canonical names must be
    used, and all datatypes are at session level. But this is
    kept in case this changes.

    The value is a Folder() class instance with
    the required fields.

    Parameters
    ----------
    name
        The display name for the datatype, that will
        be used for making and transferring files in practice.
        This should always match the canonical name, but left as
        an option for rare cases in which advanced users want to change it.

    level
        "sub" or "ses", level to make the folder at.

    """
    return {
        datatype: Folder(name=datatype, level="ses")
        for datatype in canonical_configs.get_datatypes()
    }


def get_non_sub_names() -> List[str]:
    """Return all arguments that are not allowed at the subject level.

    These are invalid as `sub_names` for data transfer.
    """
    return [
        "all_ses",
        "all_non_ses",
        "all_datatype",
        "all_non_datatype",
    ]


def get_non_ses_names() -> List[str]:
    """Return all arguments that are not allowed at the session level."""
    return [
        "all_sub",
        "all_non_sub",
        "all_datatype",
        "all_non_datatype",
    ]


def canonical_reserved_keywords() -> List[str]:
    """Return key keyword arguments passed to `sub_names` or `ses_names`."""
    return get_non_sub_names() + get_non_ses_names()


def get_top_level_folders() -> List[TopLevelFolder]:
    """Return a list of canonical top level folder names."""
    return ["rawdata", "derivatives"]


def get_datashuttle_path() -> Path:
    """Return the datashuttle path where all project configs are stored."""
    return Path.home() / ".datashuttle"


def get_project_datashuttle_path(project_name: str) -> Tuple[Path, Path]:
    """Return the datashuttle config path for the project.

    Also returns a temporary logging path used in cases when
    the `local_path` is not yet defined. The base configuration
    path is the user home directory.
    """
    base_path = get_datashuttle_path() / project_name
    temp_logs_path = base_path / "temp_logs"

    return base_path, temp_logs_path
