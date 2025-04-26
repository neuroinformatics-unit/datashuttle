from typing import Dict, Literal, Tuple, Union

from datashuttle.configs.config_class import Configs
from datashuttle.utils import rclone, utils
from datashuttle.utils.custom_exceptions import ConfigError

TopLevelFolder = Literal["rawdata", "derivatives"]


# -----------------------------------------------------------------------------
# Core Functions
# -----------------------------------------------------------------------------


def verify_gdrive_access_core(
    cfg: Configs,
) -> bool:
    """
    Verify that the Google Drive configuration is working.
    Returns True if we can successfully list files, False otherwise.
    """
    if not cfg["gdrive_folder_id"]:
        return False

    if not verify_gdrive_config_exists(cfg):
        return False

    rclone_config_name = cfg.get_rclone_config_name()

    output = rclone.call_rclone(f"lsf {rclone_config_name}:", pipe_std=True)

    return output.returncode == 0


def verify_gdrive_config_exists(cfg: Configs) -> bool:
    """
    Enhanced check for Google Drive configuration existence.
    Checks multiple possible config names.
    """
    rclone_config_name = cfg.get_rclone_config_name()

    output = rclone.call_rclone("config show", pipe_std=True)
    config_output = output.stdout.decode("utf-8")

    if rclone_config_name in config_output:
        return True

    project_name = cfg.project_name
    if any(
        name.startswith(project_name) and "drive" in config_output.lower()
        for name in config_output.split("\n")
    ):
        return True

    return False


def get_gdrive_setup_command(
    cfg: Configs,
) -> str:
    """
    Get the rclone command to run for Google Drive setup.

    Parameters
    -----------
    cfg : datashuttle config UserDict

    Returns
    -------
    command : command string to run in terminal
    """
    rclone_config_name = cfg.get_rclone_config_name()
    folder_id = cfg["gdrive_folder_id"]

    return f"rclone config create {rclone_config_name} drive root_folder_id {folder_id}"


def prompt_gdrive_setup(
    cfg: Configs,
) -> None:
    """
    Provide instructions for Google Drive setup via terminal.

    This is needed because Google Drive requires interactive browser
    authentication, which can't be easily automated within datashuttle.

    Parameters
    -----------
    cfg : datashuttle config UserDict
    """
    rclone.setup_rclone_config_for_gdrive(cfg, cfg.get_rclone_config_name())


def reset_gdrive_config(cfg: Configs) -> Tuple[bool, str]:
    """
    Google Drive configurationn it can be created.
    Returns (success, message)
    """
    rclone_config_name = cfg.get_rclone_config_name()

    try:
        rclone.call_rclone(
            f"config delete {rclone_config_name}", pipe_std=True
        )
        return (
            True,
            "Google Drive configuration reset successfully. Please set up the connection again.",
        )
    except Exception as e:
        return False, f"Error resetting configuration: {str(e)}"


def attempt_gdrive_connect(cfg: Configs) -> Tuple[bool, str]:
    """
    Try to connect to Google Drive with comprehensive checks and error reporting.
    """
    if not cfg["gdrive_folder_id"]:
        return False, "Google Drive folder ID is not configured"

    if not verify_gdrive_config_exists(cfg):
        command = f"rclone config create {cfg.get_rclone_config_name()} drive root_folder_id {cfg['gdrive_folder_id']}"
        return False, (
            f"Google Drive configuration not found. "
            f"You need to run this command in your terminal:\n{command}"
        )

    try:
        rclone_config_name = cfg.get_rclone_config_name()
        output = rclone.call_rclone(
            f"lsf {rclone_config_name}:", pipe_std=True
        )

        if output.returncode == 0:
            return True, "Successfully connected to Google Drive"
        else:
            error = output.stderr.decode("utf-8")
            if "not found" in error.lower():
                return (
                    False,
                    "Configuration exists but couldn't connect. Try resetting and creating again.",
                )
            elif "permission denied" in error.lower():
                return (
                    False,
                    "Permission denied. Check folder ID and permissions.",
                )
            else:
                return False, f"Connection error: {error.strip()}"
    except Exception as e:
        return False, f"Error during connection attempt: {str(e)}"


def verify_with_retry(
    cfg: Configs, attempts: int = 3, delay: int = 1
) -> Tuple[bool, str]:
    """
    Try verification multiple times with delay, to handle timing issues
    where the config may take a moment to be fully available.
    """
    import time

    for attempt in range(attempts):
        success, message = attempt_gdrive_connect(cfg)
        if success:
            return True, message

        if attempt < attempts - 1:
            time.sleep(delay)

    return False, message  # Return last message if all attempts fail


# -----------------------------------------------------------------------------
# Enhanced Transfer Features
# -----------------------------------------------------------------------------


def get_drive_usage(cfg: Configs) -> Tuple[bool, Union[Dict, str]]:
    """
    Get storage usage statistics from Google Drive.
    Returns (success, data) where data is either a dict with stats or an error message.
    """
    if not verify_gdrive_access_core(cfg):
        return (
            False,
            "Cannot access Google Drive. Please verify configuration.",
        )

    rclone_config_name = cfg.get_rclone_config_name()

    output = rclone.call_rclone(f"about {rclone_config_name}:", pipe_std=True)

    if output.returncode != 0:
        return (
            False,
            f"Failed to get Drive info: {output.stderr.decode('utf-8')}",
        )

    about_output = output.stdout.decode("utf-8")

    try:
        total_size = 0
        total_bytes_used = 0
        total_bytes_free = 0

        for line in about_output.splitlines():
            if "Total:" in line:
                total_part = line.split("Total:")[1].strip()
                if "(" in total_part:
                    bytes_part = total_part.split("(")[1].split(")")[0].strip()
                    if "Bytes" in bytes_part:
                        total_size = int(bytes_part.split(" ")[0])

            if "Used:" in line:
                used_part = line.split("Used:")[1].strip()
                if "(" in used_part:
                    bytes_part = used_part.split("(")[1].split(")")[0].strip()
                    if "Bytes" in bytes_part:
                        total_bytes_used = int(bytes_part.split(" ")[0])

            if "Free:" in line:
                free_part = line.split("Free:")[1].strip()
                if "(" in free_part:
                    bytes_part = free_part.split("(")[1].split(")")[0].strip()
                    if "Bytes" in bytes_part:
                        total_bytes_free = int(bytes_part.split(" ")[0])

        return True, {
            "total_size_bytes": total_size,
            "total_size_human": (
                utils.human_readable_size(total_size)
                if hasattr(utils, "human_readable_size")
                else f"{total_size} bytes"
            ),
            "used_bytes": total_bytes_used,
            "used_human": (
                utils.human_readable_size(total_bytes_used)
                if hasattr(utils, "human_readable_size")
                else f"{total_bytes_used} bytes"
            ),
            "free_bytes": total_bytes_free,
            "free_human": (
                utils.human_readable_size(total_bytes_free)
                if hasattr(utils, "human_readable_size")
                else f"{total_bytes_free} bytes"
            ),
            "usage_percent": (
                round((total_bytes_used / total_size) * 100, 2)
                if total_size > 0
                else 0
            ),
        }
    except Exception as e:
        return False, f"Failed to parse Drive size information: {str(e)}"


def verify_file_integrity(
    cfg: Configs, top_level_folder: TopLevelFolder, filepath: str
) -> Tuple[bool, str]:
    """
    Verify the integrity of a file by comparing checksums.
    """
    local_path = cfg.get_base_folder("local", top_level_folder) / filepath
    if not local_path.exists():
        return False, f"Local file does not exist: {local_path}"

    rclone_config_name = cfg.get_rclone_config_name()
    central_path_str = cfg.get_base_folder(
        "central", top_level_folder
    ).as_posix()
    remote_path = f"{rclone_config_name}:{central_path_str}/{filepath}"

    local_md5_cmd = rclone.call_rclone(f"md5sum '{local_path}'", pipe_std=True)
    if local_md5_cmd.returncode != 0:
        stderr_output = local_md5_cmd.stderr.decode("utf-8")
        return False, f"Failed to calculate local checksum: {stderr_output}"

    local_md5 = local_md5_cmd.stdout.decode("utf-8").split()[0]

    remote_md5_cmd = rclone.call_rclone(
        f"md5sum '{remote_path}'", pipe_std=True
    )
    if remote_md5_cmd.returncode != 0:
        stderr_output = remote_md5_cmd.stderr.decode("utf-8")
        return False, f"Failed to calculate remote checksum: {stderr_output}"

    remote_md5 = remote_md5_cmd.stdout.decode("utf-8").split()[0]

    if local_md5 == remote_md5:
        return True, "File integrity verified"
    else:
        return (
            False,
            f"Checksum mismatch: local={local_md5}, remote={remote_md5}",
        )


# -----------------------------------------------------------------------------
# Setup GDrive - API Wrappers
# -----------------------------------------------------------------------------


def verify_gdrive_access_with_logging(
    cfg: Configs,
    message_on_successful_connection: bool = True,
) -> bool:
    """
    Verify Google Drive access with logging.

    Parameters
    -----------
    cfg : datashuttle config UserDict

    message_on_successful_connection : whether to print success message
    """
    try:
        success = verify_gdrive_access_core(cfg)
        if success:
            if message_on_successful_connection:
                utils.print_message_to_user(
                    f"Connection to Google Drive folder '{cfg['gdrive_folder_id']}' made successfully."
                )
        else:
            if not verify_gdrive_config_exists(cfg):
                utils.log_and_raise_error(
                    "Google Drive configuration does not exist. You need to run the setup process first.",
                    ConfigError,
                )
            else:
                utils.log_and_raise_error(
                    f"Could not access Google Drive. Ensure that:\n"
                    f"1) You completed the interactive rclone setup\n"
                    f"2) The folder ID '{cfg['gdrive_folder_id']}' is correct\n"
                    f"3) You have appropriate permissions to access the folder",
                    ConfigError,
                )
        return success
    except Exception as e:
        utils.log_and_raise_error(
            f"Could not connect to Google Drive. Ensure that:\n"
            f"1) You completed the interactive rclone setup\n"
            f"2) The folder ID '{cfg['gdrive_folder_id']}' is correct\n"
            f"Error details: {str(e)}",
            ConfigError,
        )
        return False


def setup_gdrive_with_logging(
    cfg: Configs,
    log: bool = True,
) -> None:
    """
    Provide instructions for Google Drive setup with logging.

    Parameters
    -----------
    cfg : datashuttle config UserDict

    log : whether to log
    """
    try:
        command = get_gdrive_setup_command(cfg)
        prompt_gdrive_setup(cfg)

        if log:
            message = (
                f"To complete Google Drive setup, run this in your terminal:\n\n"
                f"{command}\n\n"
                f"Follow the interactive prompts to authenticate with Google."
            )
            utils.print_message_to_user(message)
            utils.log(f"\n{message}")
    except Exception as e:
        utils.log_and_raise_error(
            f"Failed to generate Google Drive setup instructions.\n"
            f"Check that the Google Drive folder ID is correctly configured.\n"
            f"Error details: {str(e)}",
            RuntimeError,
        )


def get_gdrive_connection_health(cfg: Configs) -> Dict:
    """
    Check the health of the Google Drive connection by running multiple tests.

    Returns a dictionary with test results and overall health status.
    """
    health = {
        "config_exists": False,
        "connection_ok": False,
        "folder_exists": False,
        "overall_status": "FAILED",
        "message": "",
    }

    if verify_gdrive_config_exists(cfg):
        health["config_exists"] = True
    else:
        health["message"] = (
            "Google Drive configuration not found. Run the setup process."
        )
        return health

    try:
        rclone_config_name = cfg.get_rclone_config_name()
        output = rclone.call_rclone(
            f"lsf {rclone_config_name}:", pipe_std=True
        )

        if output.returncode == 0:
            health["connection_ok"] = True
        else:
            error = output.stderr.decode("utf-8")
            if "permission denied" in error.lower():
                health["message"] = (
                    "Permission denied. Check folder permissions."
                )
            else:
                health["message"] = f"Connection error: {error.strip()}"
            return health
    except Exception as e:
        health["message"] = f"Error checking connection: {str(e)}"
        return health

    try:
        folder_id = cfg["gdrive_folder_id"]
        rclone_config_name = cfg.get_rclone_config_name()

        output = rclone.call_rclone(
            f"lsf {rclone_config_name}:", pipe_std=True
        )

        if output.returncode == 0:
            health["folder_exists"] = True
        else:
            health["message"] = (
                f"Folder with ID '{folder_id}' not found or not accessible."
            )
            return health
    except Exception as e:
        health["message"] = f"Error checking folder: {str(e)}"
        return health

    if all(
        [
            health["config_exists"],
            health["connection_ok"],
            health["folder_exists"],
        ]
    ):
        health["overall_status"] = "HEALTHY"
        health["message"] = "Google Drive connection is healthy"
    elif not health["message"]:
        health["message"] = "Google Drive connection has issues"

    return health
