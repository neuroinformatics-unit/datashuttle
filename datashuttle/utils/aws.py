import getpass
import json
import sys

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
    if not sys.stdin.isatty():
        proceed = input(
            "\nWARNING!\nThe next step is to enter a AWS secret access key, but it is not possible\n"
            "to hide your secret access key while entering it in the current terminal.\n"
            "This can occur if running the command in an IDE.\n\n"
            "Press 'y' to proceed to secret key entry. "
            "The characters will not be hidden!\n"
            "Alternatively, run AWS S3 setup after starting Python in your "
            "system terminal \nrather than through an IDE: "
        )
        if proceed != "y":
            utils.print_message_to_user(
                "Quitting AWS S3 setup as 'y' not pressed."
            )
            utils.log_and_raise_error(
                "AWS S3 setup aborted by user.", ConnectionAbortedError
            )

        aws_secret_access_key = input(
            "Please enter your AWS secret access key. Characters will not be hidden: "
        )

    else:
        aws_secret_access_key = getpass.getpass(
            "Please enter your AWS secret access key: "
        )

    if log:
        utils.log("AWS secret access key entered by user.")

    return aws_secret_access_key.strip()
