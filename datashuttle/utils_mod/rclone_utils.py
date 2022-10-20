import glob
import os.path
import shutil
import subprocess
import warnings
from pathlib import Path

from datashuttle.utils_mod import http_utils, utils


def call_rclone(command, silent=False):
    """"""
    command = (
        get_rclone_exe_path()[0] + " " + command
    )  # TODO: hacky _get_rclone_exe_path. NOTE: rlcone has HTTP API might be easier to use in future
    if silent:
        return_code = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    else:
        return_code = subprocess.run(command)
    return return_code.returncode


def get_rclone_dir(for_user=False):
    rclone_directory_name = "rclone_root_no_delete_no_overwrite_915639"  # shared directory with project names, choose something user never will
    path_ = utils.get_user_appdir_path(rclone_directory_name)
    if for_user:
        path_ = os.fspath(path_)
    return path_


def get_rclone_exe_path():
    """
    The wildcard dir contains info on the platform-dependent installation,
    as does the file ext.
    """
    paths = glob.glob(get_rclone_dir().as_posix() + "/rclone/*/rclone.*")
    executable_rclone_path = [
        path_ for path_ in paths if Path(path_).name != "rclone.1"
    ]
    return executable_rclone_path


def check_rclone_exists():
    """"""
    exe_path = glob.glob(f"{get_rclone_dir().as_posix()}/rclone/*/rclone.exe")

    if len(exe_path) not in [0, 1]:
        raise BaseException(
            f"There are two rclone.exe files in the rclone download directory.\n"
            f"Please  check {get_rclone_dir(for_user=True)}"
        )
    if not any(exe_path):
        return False
    return True


def download_rclone():
    """"""
    if os.path.isdir(get_rclone_dir()):
        delete_rclone_dir()

    utils.make_dirs(get_rclone_dir().as_posix())

    if os.name == "nt":
        zip_file_path = Path(get_rclone_dir().as_posix() + "/rclone.zip")
        http_utils.retrieve_over_http(
            "https://downloads.rclone.org/v1.59.2/rclone-v1.59.2-windows-amd64.zip",
            zip_file_path,
        )

        shutil.unpack_archive(zip_file_path, get_rclone_dir() / "rclone")
        zip_file_path.unlink()

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
            f"Could not delete entire Rclone directory at {get_rclone_dir(for_user=True)}.\n"
            f"Continuing Anyway."
        )


def prompt_rclone_download_if_does_not_exist():
    """"""
    if not check_rclone_exists():
        utils.message_user(
            f"rclone download is not found at {get_rclone_dir(for_user=True)}\n"
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
    cfg, mounted_or_ssh, rclone_config_name, ssh_key_path
):

    if mounted_or_ssh == "mounted":
        call_rclone(f"config create {rclone_config_name} local")

    elif mounted_or_ssh == "ssh":

        call_rclone(
            f"config create "
            f"{rclone_config_name} "
            f"sftp "
            f"host {cfg['remote_host_id']} "
            f"user {cfg['remote_host_username']} "
            f"port 22 "
            f"key_file {ssh_key_path}"
        )
