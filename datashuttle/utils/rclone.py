import subprocess
from pathlib import Path

from datashuttle.configs.configs import Configs


def call_rclone(command: str, silent: bool = False) -> int:
    """
    :param command: Rclone command to be run
    :param silent: if True, do not output anything to stdout.
    :return:
    """
    command = "rclone " + command
    if silent:
        return_code = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            shell=True,
        )
    else:
        return_code = subprocess.run(command, shell=True)

    return return_code.returncode


def transfer_data(
    local_filepath: str,
    remote_filepath: str,
    rclone_config_name: str,
    upload_or_download: str,
    dry_run: bool,
) -> None:
    """ """
    extra_arguments = "--create-empty-src-dirs"
    if dry_run:
        extra_arguments += " --dry-run"

    if upload_or_download == "upload":

        call_rclone(
            f"copy "
            f'"{local_filepath}" '
            f'"{rclone_config_name}:'
            f'{remote_filepath}" '
            f"{extra_arguments}"
        )

    elif upload_or_download == "download":
        call_rclone(
            f"copy "
            f'"{rclone_config_name}:'
            f'{remote_filepath}" '
            f'"{local_filepath}"  '
            f"{extra_arguments}"
        )


def setup_remote_as_rclone_target(
    cfg: Configs,
    rclone_config_name: str,
    ssh_key_path: Path,
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
        call_rclone(f"config create {rclone_config_name} local", silent=True)

    elif connection_method == "ssh":

        call_rclone(
            f"config create "
            f"{rclone_config_name} "
            f"sftp "
            f"host {cfg['remote_host_id']} "
            f"user {cfg['remote_host_username']} "
            f"port 22 "
            f"key_file {ssh_key_path.as_posix()}",
            silent=True,
        )


def check_rclone_with_default_call() -> bool:
    """"""
    try:
        return_code = call_rclone("-h", silent=True)
    except FileNotFoundError:
        return False
    return True if return_code == 0 else False


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
