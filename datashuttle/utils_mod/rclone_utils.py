import glob
import os.path
import shutil
import subprocess
import warnings
from pathlib import Path

from datashuttle.utils_mod import utils

from ..datashuttle._vendored import bg_atlasapi


def call_rclone(command: str, silent: bool = False):
    """
    :param command: Rclone command to be run
    :param silent: if True, do not output anything to stdout.
    :return:
    """
    command = get_rclone_exe_path()[0] + " " + command
    if silent:
        return_code = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    else:
        return_code = subprocess.run(command)
    return return_code.returncode


def get_rclone_dir(for_user=False):
    """
    Rclone dir is always stored on the users appdir.

    Note this is also where project dirs are stored and so
    this must never share a name with a user project.
    """
    rclone_directory_name = "rclone_root_no_delete_no_overwrite"
    path_ = utils.get_appdir_path(rclone_directory_name)
    if for_user:
        path_ = os.fspath(path_)
    return path_


def get_rclone_exe_path():
    """
    The wildcard dir contains info on the platform-dependent
    installation, as does the file ext.
    """
    paths = glob.glob(get_rclone_dir().as_posix() + "/rclone/*/rclone.*")
    executable_rclone_path = [
        path_ for path_ in paths if Path(path_).name != "rclone.1"
    ]
    return executable_rclone_path


def check_rclone_exists():
    """
    Check that the rclone executable exists in the root drive.
    """
    exe_path = glob.glob(f"{get_rclone_dir().as_posix()}/rclone/*/rclone.exe")

    if len(exe_path) not in [0, 1]:
        raise BaseException(
            f"There are two rclone.exe files in the "
            f"rclone download directory.\n"
            f"Please  check {get_rclone_dir(for_user=True)}"
        )
    if not any(exe_path):
        return False
    return True


def download_rclone():
    """
    Download Rclone to the user Appdir. This will pull
    the RClone version for the current OS.
    """
    if os.path.isdir(get_rclone_dir()):
        delete_rclone_dir()

    utils.make_dirs(get_rclone_dir().as_posix())

    if os.name == "nt":
        zip_file_path = Path(get_rclone_dir().as_posix() + "/rclone.zip")
        bg_atlasapi.retrieve_over_http(
            "https://downloads.rclone.org/v1.59.2/rclone-v1.59.2-windows-amd64.zip",  # noqa: E501
            zip_file_path,
        )

        shutil.unpack_archive(zip_file_path, get_rclone_dir() / "rclone")
        zip_file_path.unlink()

        utils.message_user("RClone successfully downloaded.")
    else:
        raise NotImplementedError("Windows rclone currently supported only.")


def check_rclone_with_default_call():
    """"""
    return_code = call_rclone("-h", silent=True)
    return True if return_code == 0 else False


def delete_rclone_dir():
    try:
        shutil.rmtree(get_rclone_dir().as_posix())
    except PermissionError:
        warnings.warn(
            f"Could not delete entire Rclone "
            f"directory at {get_rclone_dir(for_user=True)}.\n"
            f"Continuing Anyway."
        )


def prompt_rclone_download_if_does_not_exist():
    """
    Check that rclone exists on the user appdir. If it does not
    (e.g. first time using datashuttle) then download.

    Also check that the rclone is not corrupted by
    calling its --help. If it is corrupted, re-download.
    """
    if not check_rclone_exists():
        utils.message_user(
            f"rclone download is not found at "
            f"{get_rclone_dir(for_user=True)}\n"
            f"Press y to begin download."
        )
        input_ = input()
        if input_ == "y":
            download_rclone()

    if not check_rclone_with_default_call():
        utils.message_user(
            f"Rclone download corrupted at {get_rclone_dir(for_user=True)}\n"
            f"Press y to delete and re-download."
        )
        input_ = input()
        if input_ == "y":
            delete_rclone_dir()
            download_rclone()


def setup_remote_as_rclone_target(
    cfg, local_or_ssh, rclone_config_name, ssh_key_path
):
    """
    RClone sets remote targets in a config file. When
    copying to remote, use the syntax remote: to
    identify the remote to copy to.

    For local filesystem, this is just a placeholder and
    the config contains no further information.

    For SSH, this contains information for
    connecting to remote with SSH.
    """
    if local_or_ssh == "local":
        call_rclone(f"config create {rclone_config_name} local")

    elif local_or_ssh == "ssh":

        call_rclone(
            f"config create "
            f"{rclone_config_name} "
            f"sftp "
            f"host {cfg['remote_host_id']} "
            f"user {cfg['remote_host_username']} "
            f"port 22 "
            f"key_file {ssh_key_path}"
        )
