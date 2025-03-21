from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, List, Optional, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs
from datashuttle.utils import utils

import fnmatch
import os

def get_remote_gdrive_key(folder_id: str) -> Tuple[bool, str]:
    """
    Attempt to list contents of the Google Drive folder to check access.
    """
    remote_path = f"gdrive_remote:{folder_id}"
    try:
        subprocess.run(
            ["rclone", "lsf", remote_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode()

def save_gdrive_key_locally(folder_id: str, remote_name: str, central_path: Path) -> None:
    """
    Save the trusted Google Drive folder ID and remote name in the central path.
    """
    central_path.parent.mkdir(parents=True, exist_ok=True)

    with open(central_path, "w") as file:
        file.write(f"Folder ID: {folder_id}\nRemote: {remote_name}")

def connect_gdrive_with_logging(
    cfg: Configs,
    message_on_sucessful_connection: bool = True,
) -> None:
    """
    Connect to Google Drive using rclone by testing access to the remote.
    This assumes rclone has already been configured properly.
    """
    remote = cfg.get_rclone_config_name("Google Drive")

    try:
        subprocess.run(
            ["rclone", "lsf", f"{remote}:"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if message_on_sucessful_connection:
            utils.print_message_to_user(
                f"Connection to Google Drive remote '{remote}' made successfully."
            )

    except Exception as e:
        utils.log_and_raise_error(
            f"Could not connect to Google Drive. Ensure that:\n"
            f"1) You have run setup_gdrive_connection()\n"
            f"2) Your rclone remote '{remote}' is correctly configured\n"
            f"3) The folder ID exists and access is authorized.\n\n"
            f"Error:\n{e}",
            ConnectionError,
        )

def search_gdrive_remote_for_folders(
    search_path: Path,
    search_prefix: str,
    cfg: Configs,
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[List[Any], List[Any]]:
    """
    Search for the search prefix in the search path over Google Drive.
    Returns the list of matching folders, files are filtered out.

    Parameters
    -----------

    search_path : path to search for folders in

    search_prefix : search prefix for folder names e.g. "sub-*"

    cfg : project config object (provides remote and credentials)

    verbose : If `True`, if a search folder cannot be found, a message
              will be printed with the un-found path.
    """
    all_folder_names, all_filenames = get_list_of_folder_names_over_gdrive(
        cfg,
        search_path,
        search_prefix,
        verbose,
        return_full_path,
    )

    return all_folder_names, all_filenames

def get_list_of_folder_names_over_gdrive(
    cfg: Configs,
    search_path: Path,
    search_prefix: str,
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[List[Any], List[Any]]:
    """
    Use rclone to search a path over Google Drive for folders.
    Return the folder names.

    Parameters
    ----------

    cfg : datashuttle project config object

    search_path : path to search for folders in (inside the GDrive folder)

    search_prefix : prefix (can include wildcards) to search folder names

    verbose : If `True`, if a search folder cannot be found, a message
              will be printed with the un-found path.

    return_full_path : If `True`, return full rclone remote path,
                       else return only folder name
    """
    remote_path = f"{cfg.get_rclone_config_name('Google Drive')}:{search_path.as_posix()}"

    all_folder_names = []
    all_filenames = []

    try:
        result = subprocess.run(
            ["rclone", "lsjson", remote_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        entries = json.loads(result.stdout)

        for entry in entries:
            name = entry["Name"]
            is_dir = entry.get("IsDir", False)

            if fnmatch.fnmatch(name, search_prefix):
                to_append = (
                    f"{remote_path}/{name}" if return_full_path else name
                )
                if is_dir:
                    all_folder_names.append(to_append)
                else:
                    all_filenames.append(to_append)

    except subprocess.CalledProcessError as e:
        if verbose:
            utils.log_and_message(f"No file found at {remote_path}\n{e.stderr}")

    return all_folder_names, all_filenames

def verify_gdrive_remote(folder_id: str, gdrive_key_path: Path, log: bool = True) -> bool:
    """
    Prompt user to trust and save a GDrive folder ID for future use.
    """
    success, _ = get_remote_gdrive_key(folder_id)
    if not success:
        utils.print_message_to_user("Unable to access the Google Drive folder. Make sure it's shared and reachable.")
        return False

    message = (
        f"You're about to trust this Google Drive folder ID: {folder_id}\n"
        "If you trust it, type 'y' to save and proceed: "
    )
    input_ = utils.get_user_input(message)

    if input_ == "y":
        save_gdrive_key_locally(folder_id, gdrive_key_path)
        if log:
            utils.log(f"Google Drive folder ID {folder_id} trusted and saved at {gdrive_key_path}")
        utils.print_message_to_user("Google Drive folder accepted.")
        return True
    else:
        utils.print_message_to_user("Folder not accepted. No connection made.")
        return False
