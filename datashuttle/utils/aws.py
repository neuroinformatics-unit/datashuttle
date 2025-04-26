from typing import Dict, Literal, Tuple, Union

from datashuttle.configs.config_class import Configs
from datashuttle.utils import rclone, utils
from datashuttle.utils.custom_exceptions import ConfigError

TopLevelFolder = Literal["rawdata", "derivatives"]


# -----------------------------------------------------------------------------
# Core Functions
# -----------------------------------------------------------------------------


def verify_aws_credentials_core(
    cfg: Configs,
) -> bool:
    """
    Verify that AWS credentials are working by listing the bucket.
    Returns True if the bucket can be accessed, False otherwise.
    """
    bucket_name = cfg["aws_bucket_name"]
    if not bucket_name:
        return False

    rclone_config_name = cfg.get_rclone_config_name()

    output = rclone.call_rclone(
        f"lsf {rclone_config_name}:{bucket_name} --max-depth 1", pipe_std=True
    )

    return output.returncode == 0


def setup_aws_rclone_config_core(
    cfg: Configs,
) -> None:
    """
    Create or update the rclone config for AWS S3.

    Parameters
    -----------
    cfg : datashuttle config UserDict
    """
    rclone_config_name = cfg.get_rclone_config_name()
    rclone.setup_rclone_config_for_aws(cfg, rclone_config_name)


def reset_aws_config(cfg: Configs) -> Tuple[bool, str]:
    """
    AWS S3 configuration it can be created.
    Returns (success, message)
    """
    rclone_config_name = cfg.get_rclone_config_name()

    try:
        rclone.call_rclone(
            f"config delete {rclone_config_name}", pipe_std=True
        )
        return (
            True,
            "AWS configuration reset successfully. Please set up the connection again.",
        )
    except Exception as e:
        return False, f"Error resetting configuration: {str(e)}"


def check_bucket_exists(cfg: Configs) -> bool:
    """
    Check if the specified S3 bucket exists and is accessible.
    """
    bucket_name = cfg["aws_bucket_name"]
    if not bucket_name:
        return False

    rclone_config_name = cfg.get_rclone_config_name()

    output = rclone.call_rclone(f"lsf {rclone_config_name}:", pipe_std=True)

    if output.returncode != 0:
        return False

    buckets = output.stdout.decode("utf-8").splitlines()
    return bucket_name in buckets


# -----------------------------------------------------------------------------
# Enhanced Transfer Features
# -----------------------------------------------------------------------------


def get_bucket_usage(cfg: Configs) -> Tuple[bool, Union[Dict, str]]:
    """
    Get storage usage statistics from the AWS S3 bucket.
    Returns (success, data) where data is either a dict with stats or an error message.
    """
    bucket_name = cfg["aws_bucket_name"]
    if not bucket_name:
        return False, "No bucket name configured"

    rclone_config_name = cfg.get_rclone_config_name()

    output = rclone.call_rclone(
        f"size {rclone_config_name}:{bucket_name}", pipe_std=True
    )

    if output.returncode != 0:
        return (
            False,
            f"Failed to get bucket size: {output.stderr.decode('utf-8')}",
        )

    size_output = output.stdout.decode("utf-8")

    try:
        total_size = 0
        total_objects = 0

        for line in size_output.splitlines():
            if "Total size:" in line:
                size_part = line.split("Total size:")[1].strip()
                if "(" in size_part:
                    bytes_part = size_part.split("(")[1].split(")")[0].strip()
                    if "Bytes" in bytes_part:
                        total_size = int(bytes_part.split(" ")[0])

            if "Total objects:" in line:
                objects_part = line.split("Total objects:")[1].strip()
                total_objects = int(objects_part)

        return True, {
            "total_size_bytes": total_size,
            "total_size_human": (
                utils.human_readable_size(total_size)
                if hasattr(utils, "human_readable_size")
                else f"{total_size} bytes"
            ),
            "total_objects": total_objects,
        }
    except Exception as e:
        return False, f"Failed to parse bucket size information: {str(e)}"


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
        return (
            False,
            f"Failed to calculate local checksum: {local_md5_cmd.stderr.decode('utf-8')}",
        )

    local_md5 = local_md5_cmd.stdout.decode("utf-8").split()[0]

    remote_md5_cmd = rclone.call_rclone(
        f"md5sum '{remote_path}'", pipe_std=True
    )
    if remote_md5_cmd.returncode != 0:
        return (
            False,
            f"Failed to calculate remote checksum: {remote_md5_cmd.stderr.decode('utf-8')}",
        )

    remote_md5 = remote_md5_cmd.stdout.decode("utf-8").split()[0]

    if local_md5 == remote_md5:
        return True, "File integrity verified"
    else:
        return (
            False,
            f"Checksum mismatch: local={local_md5}, remote={remote_md5}",
        )


# -----------------------------------------------------------------------------
# Setup AWS - API Wrappers
# -----------------------------------------------------------------------------


def verify_aws_credentials_with_logging(
    cfg: Configs,
    message_on_successful_connection: bool = True,
) -> bool:
    """
    Verify AWS credentials with logging.

    Parameters
    -----------
    cfg : datashuttle config UserDict

    message_on_successful_connection : whether to print success message
    """
    try:
        success = verify_aws_credentials_core(cfg)
        if success:
            if message_on_successful_connection:
                utils.print_message_to_user(
                    f"Connection to AWS bucket '{cfg['aws_bucket_name']}' made successfully."
                )
        else:
            utils.log_and_raise_error(
                f"Could not access AWS bucket. Ensure that:\n"
                f"1) AWS credentials are correctly configured\n"
                f"2) The bucket '{cfg['aws_bucket_name']}' exists\n"
                f"3) You have appropriate permissions to access the bucket",
                ConfigError,
            )
        return success
    except Exception as e:
        utils.log_and_raise_error(
            f"Could not connect to AWS. Ensure that:\n"
            f"1) AWS credentials are correctly configured\n"
            f"2) The bucket '{cfg['aws_bucket_name']}' exists\n"
            f"Error details: {str(e)}",
            ConfigError,
        )
        return False


def setup_aws_rclone_config_with_logging(
    cfg: Configs,
    log: bool = True,
) -> None:
    """
    Setup AWS rclone config with logging.

    Parameters
    -----------
    cfg : datashuttle config UserDict

    log : whether to log
    """
    try:
        setup_aws_rclone_config_core(cfg)
        if log:
            success_message = f"AWS rclone config setup successfully for bucket: {cfg['aws_bucket_name']}"
            utils.print_message_to_user(success_message)
            utils.log(f"\n{success_message}")
    except Exception as e:
        utils.log_and_raise_error(
            f"Failed to setup AWS rclone config. Ensure that:\n"
            f"1) AWS credentials are correctly configured\n"
            f"2) The bucket '{cfg['aws_bucket_name']}' exists\n"
            f"Error details: {str(e)}",
            RuntimeError,
        )


def get_aws_connection_health(cfg: Configs) -> Dict:
    """
    Check the health of the AWS connection by running multiple tests.

    Returns a dictionary with test results and overall health status.
    """
    health = {
        "connection_ok": False,
        "bucket_exists": False,
        "bucket_writable": False,
        "bucket_readable": False,
        "overall_status": "FAILED",
        "message": "",
    }

    if verify_aws_credentials_core(cfg):
        health["connection_ok"] = True
    else:
        health["message"] = "Failed to connect to AWS. Check credentials."
        return health

    if check_bucket_exists(cfg):
        health["bucket_exists"] = True
    else:
        health["message"] = (
            f"Bucket '{cfg['aws_bucket_name']}' not found or not accessible."
        )
        return health

    if all([health["connection_ok"], health["bucket_exists"]]):
        health["overall_status"] = "HEALTHY"
        health["message"] = "AWS connection is healthy"
    elif not health["message"]:
        health["message"] = "AWS connection has issues with permissions"

    return health
