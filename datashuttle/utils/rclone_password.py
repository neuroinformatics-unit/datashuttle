from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datashuttle.configs.configs_class import Configs

import os
import platform
import shutil
import subprocess

from datashuttle.configs import canonical_folders
from datashuttle.utils import utils


def save_credentials_password(cfg):
    """"""
    if platform.system() == "Windows":
        set_password_windows(cfg)
    elif platform.system() == "Linux":
        set_password_linux(cfg)
    else:
        set_password_macos(cfg)


def set_password_windows(cfg: Configs):
    """"""
    password_filepath = get_password_filepath(cfg)

    if password_filepath.exists():
        password_filepath.unlink()

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

    output = subprocess.run(
        [shell, "-NoProfile", "-Command", ps_cmd],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        raise RuntimeError(
            f"\n--- STDOUT ---\n{output.stdout}",
            f"\n--- STDERR ---\n{output.stderr}",
            "Could not set the PSCredential with System.web. See the error message above.",
        )


def set_password_linux(cfg):
    """"""
    output = subprocess.run(
        "pass --help",
        shell=True,
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        raise RuntimeError(
            "`pass` is required to set password. Install e.g. sudo apt install pass."
        )

    try:
        output = subprocess.run(
            ["pass", "ls"],
            shell=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if "pass init" in e.stderr:
            raise RuntimeError(
                "Password store is not initialized. "
                "Run `pass init <gpg-id>` before using `pass`."
            )
        else:
            raise RuntimeError(
                f"\n--- STDOUT ---\n{output.stdout}",
                f"\n--- STDERR ---\n{output.stderr}",
                "Could not set up password with `pass`. See the error message above.",
            )

    output = subprocess.run(
        f"echo $(openssl rand -base64 40) | pass insert -m {cfg.rclone.get_rclone_config_name()}",
        shell=True,
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        raise RuntimeError(
            f"\n--- STDOUT ---\n{output.stdout}",
            f"\n--- STDERR ---\n{output.stderr}",
            "Could not remove the password from the RClone config. See the error message above.",
        )


def set_password_macos(cfg: Configs):
    """"""
    output = subprocess.run(
        f"security add-generic-password -a datashuttle -s {cfg.rclone.get_rclone_config_name()} -w $(openssl rand -base64 40) -U",
        shell=True,
        capture_output=True,
        text=True,
    )

    if output.returncode != 0:
        raise RuntimeError(
            f"\n--- STDOUT ---\n{output.stdout}",
            f"\n--- STDERR ---\n{output.stderr}",
            "Could not remove the password from the RClone config. See the error message above.",
        )


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
            f"/usr/bin/pass {cfg.rclone.get_rclone_config_name()}"
        )

    elif platform.system() == "Darwin":
        os.environ["RCLONE_PASSWORD_COMMAND"] = (
            f"/usr/bin/security find-generic-password -a datashuttle -s {cfg.rclone.get_rclone_config_name()} -w"
        )


def run_rclone_config_encrypt(cfg: Configs):
    """"""
    rclone_config_path = (
        cfg.rclone.get_rclone_central_connection_config_filepath()
    )

    if not rclone_config_path.exists():
        connection_method = cfg["connection_method"]

        raise RuntimeError(
            f"Rclone config file for: {connection_method} was not found. "
            f"Make sure you set up the connection first with `setup_{connection_method}_connection()`"
        )

    save_credentials_password(cfg)

    set_credentials_as_password_command(cfg)

    output = subprocess.run(
        f"rclone config encryption set --config {rclone_config_path.as_posix()}",
        shell=True,
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        raise RuntimeError(
            f"\n--- STDOUT ---\n{output.stdout}\n"
            f"\n--- STDERR ---\n{output.stderr}\n"
            "Could not remove the password from the RClone config. See the error message above."
        )

    remove_credentials_as_password_command()


def remove_rclone_password(cfg):
    """"""
    set_credentials_as_password_command(cfg)

    config_filepath = (
        cfg.rclone.get_rclone_central_connection_config_filepath()
    )

    output = subprocess.run(
        rf"rclone config encryption remove --config {config_filepath.as_posix()}",
        shell=True,
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        raise RuntimeError(
            f"\n--- STDOUT ---\n{output.stdout}",
            f"\n--- STDERR ---\n{output.stderr}",
            "Could not remove the password from the RClone config. See the error message above.",
        )

    remove_credentials_as_password_command()

    if platform.system() == "Windows":
        get_password_filepath(cfg).unlink()

    utils.log_and_message(
        f"Password removed from rclone config file: {config_filepath}"
    )


def remove_credentials_as_password_command():
    if "RCLONE_PASSWORD_COMMAND" in os.environ:
        os.environ.pop("RCLONE_PASSWORD_COMMAND")


def get_password_filepath(
    cfg,
):  # Configs  # TODO: datashuttle_path should be on configs?
    """"""
    assert cfg["connection_method"] in ["aws", "gdrive", "ssh"], (
        "password should only be set for ssh, aws, gdrive."
    )

    base_path = canonical_folders.get_datashuttle_path() / "credentials"

    base_path.mkdir(exist_ok=True, parents=True)

    return base_path / f"{cfg.rclone.get_rclone_config_name()}.xml"


def run_raise_if_fail(command, command_description):
    output = run_subprocess.run(
        command,
        shell=True,  # TODO: handle shell
        capture_output=True,
        text=True,
    )

    if output.returncode != 0:
        raise RuntimeError(
            f"\n--- STDOUT ---\n{output.stdout}\n"
            f"\n--- STDERR ---\n{output.stderr}\n"
        )


def get_password_explanation_message(
    cfg: Configs,
):  # TODO: type when other PR is merged
    """"""
    system_pass_manager = {
        "Windows": "Windows Credential Manager",
        "Linux": "the `pass` program",
        "Darwin": "macOS built-in `security` tool",
    }

    pass_type = {
        "ssh": "your private SSH key",
        "aws": "your IAM access key ID and seceret access key",
        "gdrive": "your Google Drive access token and client secret (if set)",
    }

    message = (
        f"By default, RClone stores {pass_type[cfg['connection_method']]} in plain text at the below location:\n\n"
        f"{cfg.rclone.get_rclone_central_connection_config_filepath()}\n\n"
        f"Would you like to encrypt the RClone config file using {system_pass_manager[platform.system()]}?"
    )

    return message
