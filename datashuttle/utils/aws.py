from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Tuple

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs


import fnmatch

from datashuttle.utils import utils


def get_remote_aws_key(bucket_name: str) -> Tuple[bool, str]:
    """
    Attempt to list contents of the AWS S3 bucket to check access.
    """
    remote_path = f"aws_remote:{bucket_name}"
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


def save_aws_key_locally(
    bucket_name: str, aws_region: str, central_path: Path
) -> None:
    """
    Save the AWS bucket name and region in the central path, following SSH-style storage.
    """
    central_path.parent.mkdir(parents=True, exist_ok=True)

    with open(central_path, "w") as file:
        file.write(f"Bucket: {bucket_name}\nRegion: {aws_region}")


def connect_aws_with_logging(
    cfg: Configs,
    message_on_sucessful_connection: bool = True,
) -> None:
    """
    Connect to AWS S3 using rclone by testing access to the remote.
    This assumes rclone has already been configured properly.
    """
    remote = cfg.get_rclone_config_name("AWS S3")

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
                f"Connection to AWS S3 remote '{remote}' made successfully."
            )

    except Exception as e:
        utils.log_and_raise_error(
            f"Could not connect to AWS S3. Ensure that:\n"
            f"1) You have run setup_aws_connection()\n"
            f"2) Your rclone remote '{remote}' is correctly configured\n"
            f"3) The bucket exists and credentials are valid.\n\n"
            f"Error:\n{e}",
            ConnectionError,
        )


def search_aws_remote_for_folders(
    search_path: Path,
    search_prefix: str,
    cfg: Configs,
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[List[Any], List[Any]]:
    """
    Search for the search prefix in the search path over AWS S3.
    Returns the list of matching folders, files are filtered out.

    Parameters
    -----------

    search_path : path to search for folders in

    search_prefix : search prefix for folder names e.g. "sub-*"

    cfg : project config object (provides bucket and credentials)

    verbose : If `True`, if a search folder cannot be found, a message
              will be printed with the un-found path.
    """
    all_folder_names, all_filenames = get_list_of_folder_names_over_aws(
        cfg,
        search_path,
        search_prefix,
        verbose,
        return_full_path,
    )

    return all_folder_names, all_filenames


def get_list_of_folder_names_over_aws(
    cfg: Configs,
    search_path: Path,
    search_prefix: str,
    verbose: bool = True,
    return_full_path: bool = False,
) -> Tuple[List[Any], List[Any]]:
    """
    Use rclone to search a path over AWS S3 for folders.
    Return the folder names.

    Parameters
    ----------

    cfg : datashuttle project config object

    search_path : path to search for folders in (inside the bucket)

    search_prefix : prefix (can include wildcards) to search folder names

    verbose : If `True`, if a search folder cannot be found, a message
              will be printed with the un-found path.

    return_full_path : If `True`, return full rclone remote path,
                       else return only folder name
    """
    remote_path = (
        f"{cfg.get_rclone_config_name('AWS S3')}:{search_path.as_posix()}"
    )

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
            utils.log_and_message(
                f"No file found at {remote_path}\n{e.stderr}"
            )

    return all_folder_names, all_filenames


def verify_aws_remote(
    bucket_name: str, aws_key_path: Path, log: bool = True
) -> bool:
    """
    Prompt user to trust and save an AWS S3 bucket for future use.
    """
    success, _ = get_remote_aws_key(bucket_name)
    if not success:
        utils.print_message_to_user(
            "Unable to access the AWS S3 bucket. Make sure it exists and is accessible."
        )
        return False

    message = (
        f"You're about to trust this AWS S3 bucket: {bucket_name}\n"
        "If you trust it, type 'y' to save and proceed: "
    )
    input_ = utils.get_user_input(message)

    if input_ == "y":
        save_aws_key_locally(bucket_name, aws_key_path)
        if log:
            utils.log(
                f"AWS S3 bucket {bucket_name} trusted and saved at {aws_key_path}"
            )
        utils.print_message_to_user("AWS bucket accepted.")
        return True
    else:
        utils.print_message_to_user("Bucket not accepted. No connection made.")
        return False
