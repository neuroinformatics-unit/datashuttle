from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from datashuttle.configs import canonical_configs, canonical_folders
from datashuttle.configs.config_class import Configs
from datashuttle.utils import (
    validation,
)

if TYPE_CHECKING:
    from datashuttle.utils.custom_types import (
        DisplayMode,
        TopLevelFolder,
    )


def validate_project_from_path(
    project_path: str | Path,
    top_level_folder: Optional[TopLevelFolder] = "rawdata",
    display_mode: DisplayMode = "warn",
    strict_mode: bool = False,
    validation_templates: Optional[Dict] = None,
    allow_letters_in_sub_ses_values: bool = False,
) -> List[str]:
    """Perform validation on a NeuroBlueprint-formatted project.

    Parameters
    ----------
    project_path
        Path to the project to validate. Must include the project
        name, and hold a "rawdata" or "derivatives" folder.

    top_level_folder
        The top-level folder ("rawdata" or "derivatives") to
        perform validation. If `None`, both are checked.

    display_mode
        The validation issues are displayed as ``"error"`` (raise error),
        ``"warn"`` (show warning), or ``"print"``.

    strict_mode
        If ``True``, only allow NeuroBlueprint-formatted folders to exist in
        the project. By default, non-NeuroBlueprint folders (e.g. a folder
        called 'my_stuff' in the 'rawdata') are allowed, and only folders
        starting with sub- or ses- prefix are checked. In `Strict Mode`,
        any folder not prefixed with sub-, ses- or a valid datatype will
        raise a validation issue.

    validation_templates
        A dictionary of templates for subject and session name
        to validate against. See ``DataShuttle.set_validation_templates()``
        for details.

    allow_letters_in_sub_ses_values
        If `True`, any alphanumeric character are allowed for the values associated
        with sub- or ses-  keys. Otherwise, values must be integer
        and the following additional checks are performed:

        - Labels must be the same length (e.g. sub-01 and sub-002 is invalid).

    Returns
    -------
    error_messages
        A list of validation errors found in the project.

    """
    project_path = Path(project_path)

    # Check that the project file exists and contains
    # at least one top-level folder
    if not project_path.is_dir():
        raise FileNotFoundError(
            f"Cannot perform validation. No file or folder found at `project_path`: {project_path}"
        )

    top_level_folders_to_validate = _format_top_level_folder(top_level_folder)

    # Create some mock configs for the validation call,
    # then for each top-level folder, run the validation
    # Note `get_internal_datashuttle_from_path` generates a placeholder
    # folder path but this is not actually created.
    placeholder_configs = {
        key: None for key in canonical_configs.get_canonical_configs().keys()
    }
    placeholder_configs["local_path"] = Path(project_path)  # type: ignore

    cfg = Configs(
        project_name=project_path.name,
        file_path=canonical_folders.get_internal_datashuttle_from_path(),
        input_dict=placeholder_configs,
    )

    error_messages = validation.validate_project(
        cfg=cfg,
        top_level_folder_list=top_level_folders_to_validate,
        include_central=False,
        display_mode=display_mode,
        validation_templates=validation_templates,
        strict_mode=strict_mode,
        allow_letters_in_sub_ses_values=allow_letters_in_sub_ses_values,
    )

    return error_messages


def _collect_sub_and_ses_paths(
    tlf_path: Path,
) -> tuple[list[Path], dict[str, list[Path]]]:
    """Collect subject and session folder paths within a top-level folder."""
    if not tlf_path.is_dir():
        return [], {}

    sub_dirs = [p for p in sorted(tlf_path.glob("sub-*")) if p.is_dir()]
    ses_dict: dict[str, list[Path]] = {}
    for sub in sub_dirs:
        ses_dict[sub.name] = [
            p for p in sorted(sub.glob("ses-*")) if p.is_dir()
        ]

    return sub_dirs, ses_dict


def get_all_sub_and_ses_paths_from_path(
    project_path: str | Path,
    top_level_folder: TopLevelFolder | None = "rawdata",
) -> dict[str, list[Path] | dict[str, list[Path]]]:
    """Return filepaths to all subjects and sessions directly from a project path.

    Enables discovery and inspection of NeuroBlueprint project structures with
    minimal setup, without requiring project configuration files.

    Parameters
    ----------
    project_path
        Path to the project directory. Must contain at least one top-level
        folder ('rawdata' or 'derivatives').

    top_level_folder
        The top-level folder ("rawdata" or "derivatives") to search.
        If `None`, both are checked and combined. Default is "rawdata".

    Returns
    -------
    dict
        A dictionary with "sub" key (list of Path objects for all subject folders)
        and "ses" key (dict mapping subject name to list of Path objects for its session folders).

    """
    project_path = Path(project_path)
    if not project_path.is_dir():
        raise FileNotFoundError(
            f"Cannot get paths. No directory found at `project_path`: {project_path}"
        )

    all_subs: list[Path] = []
    all_ses: dict[str, list[Path]] = {}

    for tlf in _format_top_level_folder(top_level_folder):
        sub_dirs, ses_dict = _collect_sub_and_ses_paths(project_path / tlf)
        all_subs.extend(sub_dirs)
        for sub_name, ses_dirs in ses_dict.items():
            all_ses.setdefault(sub_name, []).extend(ses_dirs)

    all_sub_paths = sorted(dict.fromkeys(all_subs), key=lambda p: p.name)
    all_ses_paths = {
        sub: sorted(dict.fromkeys(dirs), key=lambda p: p.name)
        for sub, dirs in sorted(all_ses.items())
    }
    return {"sub": all_sub_paths, "ses": all_ses_paths}


def _format_top_level_folder(
    top_level_folder: TopLevelFolder | None,
) -> List[TopLevelFolder]:
    """Format the top level folder.

    Take a `top_level_folder` ("rawdata" or "derivatives" str) and
    convert it to a list. If `None`, convert it to a list
    of both possible top-level folders.

    Parameters
    ----------
    top_level_folder
        The top-level folder to format. Can be "rawdata", "derivatives", or None.

    Returns
    -------
    A list of top-level folder names (e.g. ["rawdata"]).

    """
    rawdata_and_derivatives: List[TopLevelFolder] = ["rawdata", "derivatives"]

    formatted_top_level_folders: List[TopLevelFolder]

    if top_level_folder is None:
        formatted_top_level_folders = rawdata_and_derivatives
    else:
        if top_level_folder not in rawdata_and_derivatives:
            raise ValueError(
                f"`top_level_folder must be one of: {rawdata_and_derivatives}"
            )
        formatted_top_level_folders = [top_level_folder]

    return formatted_top_level_folders
