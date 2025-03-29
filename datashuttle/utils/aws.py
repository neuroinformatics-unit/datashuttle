import json

from datashuttle.configs.config_class import Configs
from datashuttle.utils import rclone, utils


def check_successful_connection(cfg: Configs) -> None:
    """Check for a successful connection by executing an `ls` command"""

    output = rclone.call_rclone(
        f"ls {cfg.get_rclone_config_name()}:", pipe_std=True
    )

    if output.returncode != 0:
        utils.log_and_raise_error(
            output.stderr.decode("utf-8"), ConnectionError
        )


def check_if_aws_bucket_exists(cfg: Configs) -> bool:
    output = rclone.call_rclone(
        f"lsjson {cfg.get_rclone_config_name()}:", pipe_std=True
    )

    files_and_folders = json.loads(output.stdout)

    names = list(map(lambda x: x.get("Name", None), files_and_folders))

    bucket_name = cfg["central_path"].as_posix().strip("/").split("/")[0]

    if bucket_name not in names:
        return False

    return True


# -----------------------------------------------------------------------------
# For Python API
# -----------------------------------------------------------------------------


def warn_if_bucket_absent(cfg: Configs) -> None:

    if not check_if_aws_bucket_exists(cfg):
        bucket_name = cfg["central_path"].as_posix().strip("/").split("/")[0]
        utils.print_message_to_user(
            f'WARNING: The bucket "{bucket_name}" does not exist.\n'
            f"For data transfer to happen, the bucket must exist.\n"
            f"Please change the bucket name in the `central_path`. "
        )
