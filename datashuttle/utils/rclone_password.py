import os
import platform
import shutil
import subprocess
from pathlib import Path

from datashuttle.configs import canonical_folders


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


def save_credentials_password(password_filepath: Path):
    """"""
    if platform.system() == "Windows":
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
        subprocess.run([shell, "-NoProfile", "-Command", ps_cmd], check=True)


def set_credentials_as_password_command(password_filepath: Path):
    """"""
    #    if platform.system() == "Windows":
    #        filepath = Path(filepath).resolve()

    shell = shutil.which("powershell")
    if not shell:
        raise RuntimeError("powershell.exe not found in PATH")

    # Escape single quotes inside PowerShell string by doubling them
    #  safe_path = str(filepath).replace("'", "''")

    cmd = (
        f'{shell} -NoProfile -Command "Write-Output ('
        f"[System.Runtime.InteropServices.Marshal]::PtrToStringAuto("
        f"[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR("
        f"(Import-Clixml -LiteralPath '{password_filepath.as_posix()}' ).Password)))\""
    )
    os.environ["RCLONE_PASSWORD_COMMAND"] = cmd


def set_config_password(password_filepath: Path, config_filepath: Path):
    """"""
    assert password_filepath.exists(), (
        "password file not found at point of config creation."
    )

    set_credentials_as_password_command(password_filepath)

    subprocess.run(
        f"rclone config encryption set --config {config_filepath.as_posix()} "
    )

    remove_credentials_as_password_command()


# TODO: HANDLE ERRORS
def remove_config_password(password_filepath: Path, config_filepath: Path):
    """"""
    set_credentials_as_password_command(Path(password_filepath))
    subprocess.run(
        rf"rclone config encryption remove --config {config_filepath.as_posix()}"
    )

    # TODO: HANDLE ERRORS
    remove_credentials_as_password_command()


def remove_credentials_as_password_command():
    if "RCLONE_PASSWORD_COMMAND" in os.environ:
        os.environ.pop("RCLONE_PASSWORD_COMMAND")
