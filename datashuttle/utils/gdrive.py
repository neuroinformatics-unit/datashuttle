from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from datashuttle.configs.config_class import Configs

from typing import Any, List, Tuple

from datashuttle.utils import utils


# Generic function
def search_gdrive_central_for_folders(
    search_path: Path,
    search_prefix: str,
    cfg: Configs,
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[List[Any], List[Any]]:

    command = (
        "rclone lsjson "
        f"{cfg.get_rclone_config_name()}:{search_path.as_posix()} "
        f'--include "{search_prefix}"',
    )
    output = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    all_folder_names: List[str] = []
    all_filenames: List[str] = []

    if output.returncode != 0:
        if verbose:
            utils.log_and_message(
                f"Error searching files at {search_path.as_posix()} \n {output.stderr.decode("utf-8") if output.stderr else ""}"
            )
        return all_folder_names, all_filenames

    files_and_folders = json.loads(output.stdout)

    try:
        for file_or_folder in files_and_folders:
            name = file_or_folder["Name"]
            is_dir = file_or_folder.get("IsDir", False)

            to_append = (
                (search_path / name).as_posix() if return_full_path else name
            )

            if is_dir:
                all_folder_names.append(to_append)
            else:
                all_filenames.append(to_append)

    except Exception:
        if verbose:
            utils.log_and_message(
                f"Error searching files at {search_path.to_posix()}"
            )

    return all_folder_names, all_filenames
