from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import yaml

from datashuttle.configs import canonical_configs, canonical_folders
from datashuttle.configs.config_class import Configs
from datashuttle.utils import (
    ds_logger,
    utils,
    validation,
)
from datashuttle.utils.custom_exceptions import (
    ConfigError,
    NeuroBlueprintError,
)

if TYPE_CHECKING:
    from datashuttle.utils.custom_types import (
        DisplayMode,
        TopLevelFolder,
    )


def delete_project_from_disk(
    project_name: str,
    soft_delete: bool = True,
    retention_days: int = 30,
    confirm_project_name: Optional[str] = None,
) -> None:
    """Delete a datashuttle project configuration from disk.

    By default, performs a soft-delete by moving the project's
    configuration to the `.trash` directory with an expiration date.
    If `soft_delete` is `False`, the project configuration and associated
    RClone configs are permanently deleted immediately.

    Parameters
    ----------
    project_name
        The name of the project to delete.

    soft_delete
        If `True`, move the project to `.trash` for the retention period.
        If `False`, permanently delete immediately. Default is `True`.

    retention_days
        Number of days to keep the project in trash before expiration. Default is 30.

    confirm_project_name
        Optional project name confirmation. If provided (recommended for permanent deletion),
        must match `project_name` exactly.

    """
    if not isinstance(project_name, str) or not project_name.strip():
        utils.log_and_raise_error(
            "The project name must be a non-empty string.",
            NeuroBlueprintError,
        )

    if (
        confirm_project_name is not None
        and confirm_project_name != project_name
    ):
        utils.log_and_raise_error(
            f"Project name confirmation failed. "
            f"Provided '{confirm_project_name}', expected '{project_name}'.",
            NeuroBlueprintError,
        )

    ds_logger.close_log_filehandler()

    project_path, _ = canonical_folders.get_project_datashuttle_path(
        project_name
    )

    if not project_path.is_dir():
        utils.log_and_raise_error(
            f"Cannot delete project '{project_name}'. "
            f"No project configuration found at '{project_path}'.",
            FileNotFoundError,
        )

    if soft_delete:
        trash_dir = canonical_folders.get_trash_path()
        trash_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        timestamp = now.strftime("%Y%m%dT%H%M%S")
        expires_at = now + timedelta(days=retention_days)

        trash_target = trash_dir / f"{project_name}__deleted_{timestamp}"
        if trash_target.exists():
            shutil.rmtree(trash_target)

        shutil.move(str(project_path), str(trash_target))

        metadata = {
            "original_project_name": project_name,
            "deleted_at": now.isoformat(),
            "retention_days": retention_days,
            "expires_at": expires_at.isoformat(),
        }
        meta_file = trash_target / ".deletion_metadata.yaml"
        with open(meta_file, "w") as f:
            yaml.dump(metadata, f, sort_keys=False)

        utils.print_message_to_user(
            f"Project '{project_name}' moved to Trash ({retention_days}-day retention) at '{trash_target}'."
        )
    else:
        _permanent_delete_project_files(project_name, project_path)


def _permanent_delete_project_files(
    project_name: str, project_path: Path
) -> None:
    """Permanently delete project config folder and associated RClone config files."""
    rclone_config_dir = canonical_folders.get_rclone_config_base_path()
    if rclone_config_dir.is_dir():
        for conf_file in rclone_config_dir.glob(
            f"central_{project_name}_*.conf"
        ):
            try:
                conf_file.unlink()
            except OSError:
                pass

    if project_path.is_dir():
        try:
            shutil.rmtree(project_path)
        except OSError as e:
            utils.log_and_raise_error(
                f"Failed to delete project folder at '{project_path}': {e}",
                RuntimeError,
            )

    utils.print_message_to_user(
        f"Project '{project_name}' configuration permanently deleted from '{project_path}'."
    )


def restore_project_from_trash(project_name: str) -> None:
    """Restore a soft-deleted project from the Recycle Bin back to active status.

    Parameters
    ----------
    project_name
        The name of the project to restore.

    """
    if not isinstance(project_name, str) or not project_name.strip():
        utils.log_and_raise_error(
            "The project name must be a non-empty string.",
            NeuroBlueprintError,
        )

    target_active_path, _ = canonical_folders.get_project_datashuttle_path(
        project_name
    )
    if target_active_path.is_dir():
        utils.log_and_raise_error(
            f"Cannot restore project '{project_name}'. "
            f"An active project with that name already exists at '{target_active_path}'.",
            ConfigError,
        )

    trash_dir = canonical_folders.get_trash_path()
    matching_trash_folders: List[Path] = []
    if trash_dir.is_dir():
        for item in trash_dir.iterdir():
            if item.is_dir():
                meta_file = item / ".deletion_metadata.yaml"
                if meta_file.is_file():
                    try:
                        with open(meta_file, "r") as f:
                            meta = yaml.safe_load(f)
                        if meta.get("original_project_name") == project_name:
                            matching_trash_folders.append(item)
                    except Exception:
                        pass
                elif item.name.startswith(f"{project_name}__deleted_"):
                    matching_trash_folders.append(item)

    if not matching_trash_folders:
        utils.log_and_raise_error(
            f"Cannot restore project '{project_name}'. "
            f"No matching project found in trash.",
            FileNotFoundError,
        )

    matching_trash_folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    trash_source = matching_trash_folders[0]

    shutil.move(str(trash_source), str(target_active_path))

    meta_file = target_active_path / ".deletion_metadata.yaml"
    if meta_file.is_file():
        try:
            meta_file.unlink()
        except OSError:
            pass

    utils.print_message_to_user(
        f"Project '{project_name}' successfully restored to '{target_active_path}'."
    )


def get_deleted_projects() -> List[Dict]:
    """Return a list of soft-deleted projects in the Recycle Bin.

    Returns
    -------
    List[Dict]
        List of dictionaries with metadata for each deleted project,
        sorted with the most recently deleted first.

    """
    trash_dir = canonical_folders.get_trash_path()
    if not trash_dir.is_dir():
        return []

    deleted_projects: List[Dict] = []
    now = datetime.now()

    for item in trash_dir.iterdir():
        if not item.is_dir():
            continue

        meta_file = item / ".deletion_metadata.yaml"
        if meta_file.is_file():
            try:
                with open(meta_file, "r") as f:
                    meta = yaml.safe_load(f)
                orig_name = meta.get(
                    "original_project_name",
                    item.name.split("__deleted_")[0],
                )
                deleted_at = meta.get("deleted_at", "")
                expires_at_str = meta.get("expires_at", "")
                retention_days = meta.get("retention_days", 30)

                remaining_days = 0
                if expires_at_str:
                    exp_dt = datetime.fromisoformat(expires_at_str)
                    remaining = (exp_dt - now).total_seconds() / 86400.0
                    remaining_days = max(0, int(remaining))
            except Exception:
                orig_name = item.name.split("__deleted_")[0]
                deleted_at = ""
                expires_at_str = ""
                retention_days = 30
                remaining_days = 0
        else:
            orig_name = item.name.split("__deleted_")[0]
            deleted_at = ""
            expires_at_str = ""
            retention_days = 30
            remaining_days = 0

        deleted_projects.append(
            {
                "project_name": orig_name,
                "trash_folder_name": item.name,
                "path": item,
                "deleted_at": deleted_at,
                "expires_at": expires_at_str,
                "retention_days": retention_days,
                "remaining_days": remaining_days,
            }
        )

    deleted_projects.sort(key=lambda x: str(x["deleted_at"]), reverse=True)
    return deleted_projects


def delete_expired_trash() -> List[str]:
    """Delete soft-deleted projects whose retention period has expired.

    Returns
    -------
    List[str]
        List of project names that were permanently removed.

    """
    trash_dir = canonical_folders.get_trash_path()
    if not trash_dir.is_dir():
        return []

    now = datetime.now()
    deleted_projects: List[str] = []

    for item in list(trash_dir.iterdir()):
        if not item.is_dir():
            continue

        meta_file = item / ".deletion_metadata.yaml"
        should_delete = False
        project_name = item.name.split("__deleted_")[0]

        if meta_file.is_file():
            try:
                with open(meta_file, "r") as f:
                    meta = yaml.safe_load(f)
                project_name = meta.get("original_project_name", project_name)
                expires_at_str = meta.get("expires_at", "")
                if expires_at_str:
                    exp_dt = datetime.fromisoformat(expires_at_str)
                    if now >= exp_dt:
                        should_delete = True
            except Exception:
                pass

        if should_delete:
            _permanent_delete_project_files(project_name, item)
            deleted_projects.append(project_name)

    return deleted_projects


def empty_trash() -> None:
    """Permanently delete all projects in the Recycle Bin."""
    trash_dir = canonical_folders.get_trash_path()
    if not trash_dir.is_dir():
        return

    for item in list(trash_dir.iterdir()):
        if item.is_dir():
            project_name = item.name.split("__deleted_")[0]
            _permanent_delete_project_files(project_name, item)


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
