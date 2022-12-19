import subprocess
from pathlib import Path
from subprocess import CompletedProcess

from datashuttle.configs.configs import Configs
from datashuttle.utils import utils


def call_rclone(command: str, pipe_std: bool = False) -> CompletedProcess:
    """
    :param command: Rclone command to be run
    :param silent: if True, do not output anything to stdout.
    :return:
    """
    command = "rclone " + command
    if pipe_std:
        output = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
    else:
        output = subprocess.run(command, shell=True)
    return output


def transfer_data(
    local_filepath: str,
    remote_filepath: str,
    rclone_config_name: str,
    upload_or_download: str,
    dry_run: bool,
) -> None:
    """
    Call Rclone copy command with appropriate
    arguments to execute data transfer.
    """
    extra_arguments = rclone_args("create_empty_src_dirs")

    if dry_run:
        extra_arguments += f" {rclone_args('dry_run')}"

    if upload_or_download == "upload":

        call_rclone(
            f"{rclone_args('copy')} "
            f'"{local_filepath}" '
            f'"{rclone_config_name}:'
            f'{remote_filepath}" '
            f"{extra_arguments}"
        )

    elif upload_or_download == "download":
        call_rclone(
            f"{rclone_args('copy')} "
            f'"{rclone_config_name}:'
            f'{remote_filepath}" '
            f'"{local_filepath}"  '
            f"{extra_arguments}"
        )


def setup_remote_as_rclone_target(
    cfg: Configs,
    rclone_config_name: str,
    ssh_key_path: Path,
    log: bool = False,
) -> None:
    """
    RClone sets remote targets in a config file. When
    copying to remote, use the syntax remote: to
    identify the remote to copy to.

    For local filesystem, this is just a placeholder and
    the config contains no further information.

    For SSH, this contains information for
    connecting to remote with SSH.
    """
    connection_method = cfg["connection_method"]

    if connection_method == "local_filesystem":
        call_rclone(f"config create {rclone_config_name} local", pipe_std=True)

    elif connection_method == "ssh":

        call_rclone(
            f"config create "
            f"{rclone_config_name} "
            f"sftp "
            f"host {cfg['remote_host_id']} "
            f"user {cfg['remote_host_username']} "
            f"port 22 "
            f"key_file {ssh_key_path.as_posix()}",
            pipe_std=True,
        )

    output = call_rclone("config file", pipe_std=True)

    if log:
        utils.log(
            f"Successfully created rclone config. "
            f"{output.stdout.decode('utf-8')}"
        )


def check_rclone_with_default_call() -> bool:
    """
    Check to see whether rclone is installed.
    """
    try:
        output = call_rclone("-h", pipe_std=True)
    except FileNotFoundError:
        return False
    return True if output.returncode == 0 else False


def prompt_rclone_download_if_does_not_exist() -> None:
    """
    Check that rclone exists on the user appdir. If it does not
    (e.g. first time using datashuttle) then download.

    Also check that the rclone is not corrupted by
    calling its --help. If it is corrupted, re-download.
    """
    if not check_rclone_with_default_call():
        raise BaseException(
            "RClone installation not found. Install by entering "
            "the following into your terminal:\n"
            " conda install -c conda-forge rclone"
        )


def rclone_args(name: str) -> str:
    """
    Central function to hold rclone commands
    """
    if name == "dry_run":
        arg = "--dry-run"

    if name == "create_empty_src_dirs":
        arg = "--create-empty-src-dirs"

    if name == "copy":
        arg = "copy"

    return arg
