from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from datashuttle.utils.custom_types import (
        DisplayMode,
        TopLevelFolder,
    )

from pathlib import Path
from typing import (
    Optional,
)

from datashuttle.configs import (
    canonical_configs,
)
from datashuttle.configs.config_class import Configs
from datashuttle.utils import (
    validation,
)


def quick_validate_project(
    project_path: str | Path,
    top_level_folder: Optional[TopLevelFolder] = "rawdata",
    display_mode: DisplayMode = "warn",
    strict_mode: bool = False,
    name_templates: Optional[Dict] = None,
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

    name_templates
        A dictionary of templates for subject and session name
        to validate against. See ``DataShuttle.set_name_templates()``
        for details.

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
    placeholder_configs = {
        key: None for key in canonical_configs.get_canonical_configs().keys()
    }
    placeholder_configs["local_path"] = Path(project_path)  # type: ignore

    cfg = Configs(
        project_name=project_path.name,
        file_path=None,  # type: ignore
        input_dict=placeholder_configs,
    )

    error_messages = validation.validate_project(
        cfg=cfg,
        top_level_folder_list=top_level_folders_to_validate,
        include_central=False,
        display_mode=display_mode,
        name_templates=name_templates,
        strict_mode=strict_mode,
    )

    return error_messages


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
