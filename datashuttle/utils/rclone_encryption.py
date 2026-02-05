"""Module for encrypting the RClone config file.

Methods based on: https://rclone.org/docs/#configuration-encryption.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from datashuttle.configs.configs_class import Configs

import os
import platform
import shutil
import subprocess

from datashuttle.utils import utils


def save_credentials_password(cfg: Configs) -> None:
    """Use the system password manager to set up a password for the Rclone config file encryption."""
    if platform.system() == "Windows":
        set_password_windows(cfg)
    elif platform.system() == "Linux":
        set_password_linux(cfg)
    else:
        set_password_macos(cfg)


def set_password_windows(cfg: Configs) -> None:
    """Generate and securely store a random password in a Windows Credential XML file.

    Use PowerShell to create a random password associated with the name 'rclone'.
    The password is stored as a PowerShell `PSCredential` object that can only
    be decrypted by the same Windows user account that created it.

    This password is later used to encrypt the Rclone config file.
    """
    password_filepath = get_windows_password_filepath(cfg)

    if password_filepath.exists():
        password_filepath.unlink()

    shell = shutil.which("powershell")
    if shell is None:
        utils.log_and_raise_error(
            "powershell.exe not found in PATH (need Windows PowerShell 5.1).",
            RuntimeError,
        )

    ps_cmd = (
        "Add-Type -AssemblyName System.Web; "
        "New-Object PSCredential 'rclone', "
        "(ConvertTo-SecureString ([System.Web.Security.Membership]::GeneratePassword(40,10)) -AsPlainText -Force) "
        f"| Export-Clixml -LiteralPath '{password_filepath}'"
    )

    output = subprocess.run(
        [shell, "-NoProfile", "-Command", ps_cmd],  # type: ignore
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        utils.log_and_raise_error(
            f"\n--- STDOUT ---\n{output.stdout}"
            f"\n--- STDERR ---\n{output.stderr}"
            "\nCould not set the PSCredential with System.web. See the error message above.",
            RuntimeError,
        )


def set_password_linux(cfg: Configs) -> None:
    """Generate and securely store a random password using the Linux `pass` utility.

    This function generates a random password and stores it in the user's
    GPG-encrypted password store via the `pass` command-line tool.

    The `pass` utility must be installed and initialized with a GPG ID on the
    current user account (via `pass init <gpg-id>`). If it is not initialized,
    a RuntimeError will be raised.
    """
    output = subprocess.run(
        "pass --help",
        shell=True,
        capture_output=True,
        text=True,
    )

    if output.returncode != 0:
        utils.log_and_raise_error(
            pass_error_message(
                output, include_stacktrace=False, include_install_section=True
            ),
            RuntimeError,
        )

    output = subprocess.run(
        "pass ls",
        shell=True,
        capture_output=True,
        text=True,
    )

    if output.returncode != 0:
        if "pass init" in output.stderr:
            utils.log_and_raise_error(
                f"Password store is not initialized. See below for full instructions.\n\n"
                f"{pass_error_message(output, include_stacktrace=False)}",
                RuntimeError,
            )
        else:
            utils.log_and_raise_error(
                pass_error_message(output),
                RuntimeError,
            )

    output = subprocess.run(
        f"echo $(openssl rand -base64 40) | pass insert -m {cfg.rclone.get_rclone_config_name()}",
        shell=True,
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        utils.log_and_raise_error(
            pass_error_message(output),
            RuntimeError,
        )


def pass_error_message(
    output, include_stacktrace=False, include_install_section=False
):
    """Create a detailed message on how to set up `pass`."""
    if include_install_section:
        install_section = (
            "If `pass` is not installed, install with:\nsudo apt install pass.\n\n"
            "To set up a gpg key:\n"
        )
    else:
        install_section = ""

    error_message = (
        "Could not set up a password using the `pass` password manager.\n\n"
        "This usually means `pass` has not been initialized with a GPG key.\n\n"
        f"{install_section}"
        " 1) Check whether you have an existing GPG key:\n"
        "gpg --list-secret-keys --keyid-format=long\n"
        " 2) If not, set a key with:\n"
        "gpg --full-generate-key\n"
        " 3) Initialize your key:\n"
        "pass init <gpg-key-id>\n"
    )
    if include_stacktrace:
        error_message += (
            f"Full error output:\n"
            f"--- STDOUT ---\n{output.stdout}\n"
            f"--- STDERR ---\n{output.stderr}"
        )

    return error_message


def set_password_macos(cfg: Configs) -> None:
    """Generate and store a password using the macOS Keychain.

    This function generates a random password and stores it in the macOS Keychain
    using the built-in `security` command-line tool.

    The password is generated using OpenSSL with 40 random base64 characters and
    is securely saved to the user's login Keychain.
    """
    output = subprocess.run(
        f"security add-generic-password -a datashuttle -s {cfg.rclone.get_rclone_config_name()} -w $(openssl rand -base64 40) -U",
        shell=True,
        capture_output=True,
        text=True,
    )

    if output.returncode != 0:
        utils.log_and_raise_error(
            f"\n--- STDOUT ---\n{output.stdout}"
            f"\n--- STDERR ---\n{output.stderr}"
            "\nCould not store the password in the macOS Keychain. See the error message above.",
            RuntimeError,
        )


def set_credentials_as_password_command(cfg: Configs) -> None:
    """Configure the RClone password retrieval command based on the operating system.

    This function sets the `RCLONE_PASSWORD_COMMAND` environment variable so that
    RClone can securely retrieve stored credentials

    - Windows : Uses PowerShell to decrypt a previously exported `PSCredential`
      object from the `.clixml` file created by `set_password_windows()`.
    - Linux : Uses the `pass` command-line utility to fetch the stored password
      from the user's GPG-encrypted password store.
    - macOS : Uses the built-in `security` tool to read the password
      from the user's Keychain, associated with the account name `datashuttle` and
      the rclone service name.
    """
    if platform.system() == "Windows":
        password_filepath = get_windows_password_filepath(cfg)

        assert password_filepath.exists(), (
            "Critical error: password file not found when setting password command."
        )

        shell = shutil.which("powershell")
        if not shell:
            utils.log_and_raise_error(
                "powershell.exe not found in PATH", RuntimeError
            )

        # Escape single quotes inside PowerShell string by doubling them
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


def run_rclone_config_encrypt(cfg: Configs) -> None:
    """Encrypt the rclone config file using an OS-native secret.

    This function:
      1) Generates/stores a random password using the platform-specific backend
         (Windows PSCredential, Linux `pass`, or macOS Keychain) via
         `save_credentials_password(cfg)`.
      2) Sets `RCLONE_PASSWORD_COMMAND` so rclone can retrieve the secret on demand
         via `set_credentials_as_password_command(cfg)`.
      3) Runs `rclone config encryption set --config <path>` to encrypt the config.
      4) Cleans up by removing the password command environment variable with
         `remove_rclone_password_env_var()`.
    """
    rclone_config_path = (
        cfg.rclone.get_rclone_central_connection_config_filepath()
    )

    if not rclone_config_path.exists():
        connection_method = cfg["connection_method"]

        utils.log_and_raise_error(
            f"Rclone config file for: {connection_method} was not found. "
            f"Make sure you set up the connection first with `setup_{connection_method}_connection()`",
            RuntimeError,
        )

    save_credentials_password(cfg)

    set_credentials_as_password_command(cfg)

    output = subprocess.run(
        f'rclone config encryption set --config "{str(rclone_config_path)}"',
        shell=True,
        capture_output=True,
        text=True,
    )

    remove_rclone_password_env_var()

    if output.returncode != 0:
        utils.log_and_raise_error(
            f"\n--- STDOUT ---\n{output.stdout}\n"
            f"\n--- STDERR ---\n{output.stderr}\n"
            "\nCould not encrypt the RClone config. See the error message above.",
            RuntimeError,
        )


def remove_rclone_encryption(cfg: Configs) -> None:
    """Remove encryption from a Rclone config file.

    Set the credentials one last time to remove encryption from
    the RClone config file. Once removed, clean up the password
    as stored with the system credential manager.
    """
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

    remove_rclone_password_env_var()

    if output.returncode != 0:
        utils.log_and_raise_error(
            f"\n--- STDOUT ---\n{output.stdout}"
            f"\n--- STDERR ---\n{output.stderr}"
            "\nCould not remove the password from the RClone config. See the error message above.",
            RuntimeError,
        )

    if platform.system() == "Windows":
        password_filepath = get_windows_password_filepath(cfg)
        if password_filepath.exists():
            password_filepath.unlink()

    elif platform.system() == "Linux":
        name = cfg.rclone.get_rclone_config_name()
        subprocess.run(
            ["pass", "rm", "-f", name],
            check=False,
        )

    elif platform.system() == "Darwin":
        service = cfg.rclone.get_rclone_config_name()
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-a",
                "datashuttle",
                "-s",
                service,
            ],
            check=False,
        )

    utils.log_and_message(
        f"Password removed from rclone config file: {config_filepath}"
    )


def remove_rclone_password_env_var():
    """Tidy up the rclone password environment variable."""
    if "RCLONE_PASSWORD_COMMAND" in os.environ:
        os.environ.pop("RCLONE_PASSWORD_COMMAND")


def connection_method_requires_encryption(connection_method: str):
    """Check whether the connection method stores sensitive information."""
    return connection_method in ["aws", "gdrive", "ssh"]


def get_windows_password_filepath(
    cfg: Configs,
) -> Path:
    """Get the canonical location where datashuttle stores the windows credentials."""
    assert connection_method_requires_encryption(cfg["connection_method"])

    # Put this folder next to the project (datashuttle) config file
    base_path = cfg.file_path.parent / "credentials"

    base_path.mkdir(exist_ok=True, parents=True)

    return base_path / f"{cfg.rclone.get_rclone_config_name()}.xml"


def get_explanation_message(
    cfg: Configs,
) -> str:
    """Explaining Rclone's default credential storage and OS-specific encryption options.

    Displayed in both the Python API and the TUI.
    """
    system_pass_manager = {
        "Windows": "PSCredential",
        "Linux": "the `pass` program",
        "Darwin": "macOS built-in `security` tool",
    }

    pass_type = {
        "ssh": "private SSH key",
        "aws": "IAM access key ID and secret access key",
        "gdrive": "Google Drive access token and client secret (if set)",
    }

    message = (
        f"By default, RClone stores your {pass_type[cfg['connection_method']]} in plain text at the below location:\n\n"
        f"{cfg.rclone.get_rclone_central_connection_config_filepath()}\n\n"
        f"Would you like to encrypt the RClone config file using {system_pass_manager[platform.system()]}?"
    )

    return message
