import os
import platform
import shutil
import subprocess
from pathlib import Path

from configs.config_class import Configs

from datashuttle.configs import canonical_folders
from datashuttle.utils import utils


def get_password_filepath(
    cfg,
):  # Configs  # TOOD: datashuttle_path should be on configs?
    """"""
    assert cfg["connection_method"] in ["aws", "gdrive", "ssh"], (
        "password should only be set for ssh, aws, gdrive."
    )

    base_path = canonical_folders.get_datashuttle_path() / "credentials"

    base_path.mkdir(exist_ok=True, parents=True)

    return base_path / f"{cfg.get_rclone_config_name()}.xml"


def save_credentials_password(cfg):
    """"""
    if platform.system() == "Windows":
        password_filepath = get_password_filepath(cfg)

        if password_filepath.exists():
            password_filepath.unlink()

        # $env:APPDATA\\rclone\\rclone-credential.xml
        shell = shutil.which("powershell")
        if not shell:
            raise RuntimeError(
                "powershell.exe not found in PATH (need Windows PowerShell 5.1)."
            )

        ps_cmd = (
            "Add-Type -AssemblyName System.Web; "
            "New-Object PSCredential 'rclone', "
            "(ConvertTo-SecureString ([System.Web.Security.Membership]::GeneratePassword(40,10)) -AsPlainText -Force) "
            f"| Export-Clixml -LiteralPath '{password_filepath}'"
        )

        # run it
        # TODO: HANDLE ERRORS
        subprocess.run([shell, "-NoProfile", "-Command", ps_cmd], check=True)

    elif platform.system() == "Linux":
        output = subprocess.run("pass --help", shell=True, capture_output=True)

        if output.returncode != 0:
            raise RuntimeError(
                "`pass` is required to set password. Install e.g. sudo apt install pass."
            )

        try:
            # TODO: HANDLE ERRORS
            result = subprocess.run(
                ["pass", "ls"], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            if "pass init" in e.stderr:
                raise Exception()  # re-raise unexpected errors

        breakpoint()
        # TODO: HANDLE ERRORS
        subprocess.run(
            f"echo $(openssl rand -base64 40) | pass insert -m {cfg.get_rclone_config_name()}",
            shell=True,
            check=True,
        )

    # TODO: HANDLE ERRORS
    else:
        # TODO: HANDLE ERRORS
        subprocess.run(
            f"security add-generic-password -a datashuttle -s {cfg.get_rclone_config_name()} -w $(openssl rand -base64 40) -U",
            shell=True,
            check=True,
        )


def name_from_file(password_filepath):  # TODO: HADNLE THIS MUCH LESS WEIRDLY!
    """"""
    return f"datashuttle/rclone/{password_filepath.stem}"


def set_credentials_as_password_command(cfg):
    """"""
    if platform.system() == "Windows":
        password_filepath = get_password_filepath(cfg)

        assert password_filepath.exists(), (
            "Critical error: password file not found when setting password command."
        )

        shell = shutil.which("powershell")
        if not shell:
            raise RuntimeError("powershell.exe not found in PATH")

        # Escape single quotes inside PowerShell string by doubling them
        #  safe_path = str(filepath).replace("'", "''")

        cmd = (
            f'{shell} -NoProfile -Command "Write-Output ('
            f"[System.Runtime.InteropServices.Marshal]::PtrToStringAuto("
            f"[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR("
            f"(Import-Clixml -LiteralPath '{password_filepath}' ).Password)))\""
        )
        os.environ["RCLONE_PASSWORD_COMMAND"] = cmd

    elif platform.system() == "Linux":
        os.environ["RCLONE_PASSWORD_COMMAND"] = (
            f"/usr/bin/pass {cfg.get_rclone_config_name()}"
        )

    elif platform.system() == "Darwin":
        os.environ["RCLONE_PASSWORD_COMMAND"] = (
            f"/usr/bin/security find-generic-password -a datashuttle -s {cfg.get_rclone_config_name()} -w"
        )


def run_rclone_config_encrypt(cfg: Configs):
    """"""
    rclone_config_path = cfg.get_rclone_config_filepath()

    if not rclone_config_path.exists():
        connection_method = cfg["connection_method"]

        raise RuntimeError(
            f"Rclone config file for: {connection_method} was not found. "
            f"Make sure you set up the connection first with `setup_{connection_method}_connection()`"
        )

    save_credentials_password(cfg)

    set_credentials_as_password_command(cfg)

    # TODO: HANDLE ERRORS
    subprocess.run(
        f"rclone config encryption set --config {rclone_config_path.as_posix()}",
        shell=True,
    )

    remove_credentials_as_password_command()


# TODO: HANDLE ERRORS
def remove_rclone_password(cfg):
    """"""
    set_credentials_as_password_command(Path(cfg))

    config_filepath = cfg.get_rclone_config_filepath()

    # TODO: HANDLE ERRORS
    subprocess.run(
        rf"rclone config encryption remove --config {config_filepath.as_posix()}",
        shell=True,
    )

    remove_credentials_as_password_command()

    utils.log_and_message(
        f"Password removed from rclone config file: {config_filepath}"
    )


def remove_credentials_as_password_command():
    if "RCLONE_PASSWORD_COMMAND" in os.environ:
        os.environ.pop("RCLONE_PASSWORD_COMMAND")
