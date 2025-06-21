import json

from datashuttle.configs.config_class import Configs
from datashuttle.utils import rclone, utils
from datashuttle.utils.custom_exceptions import ConfigError


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


def raise_if_bucket_absent(cfg: Configs) -> None:
    if not check_if_aws_bucket_exists(cfg):
        bucket_name = cfg["central_path"].as_posix().strip("/").split("/")[0]
        utils.log_and_raise_error(
            f'The bucket "{bucket_name}" does not exist.\n'
            f"For data transfer to happen, the bucket must exist.\n"
            f"Please change the bucket name in the `central_path`.",
            ConfigError,
        )


# -----------------------------------------------------------------------------
# For Python API
# -----------------------------------------------------------------------------


def get_aws_secret_access_key(log: bool = True) -> str:
    aws_secret_access_key = utils.get_connection_secret_from_user(
        connection_method_name="AWS",
        key_name_full="AWS secret access key",
        key_name_short="secret key",
        log_status=log,
    )

    return aws_secret_access_key.strip()
