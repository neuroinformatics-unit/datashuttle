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

    elif platform.system() == "Linux":
        output = subprocess.run("pass --help", shell=True, capture_output=True)

        if output.returncode != 0:
            raise RuntimeError(
                "`pass` is required to set password. Install e.g. sudo apt install pass."
            )

        try:
            result = subprocess.run(
                ["pass", "ls"], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            if "pass init" in e.stderr:
                raise Exception()  # re-raise unexpected errors

        breakpoint()
        subprocess.run(
            f"echo $(openssl rand -base64 40) | pass insert -m {name_from_file(password_filepath)}",
            shell=True,
            check=True,
        )

    # TODO: HANDLE ERRORS
    else:
        subprocess.run(
            f"security add-generic-password -a datashuttle -s {name_from_file(password_filepath)} -w $(openssl rand -base64 40) -U",
            shell=True,
            check=True,
        )


def name_from_file(password_filepath):  # TODO: HADNLE THIS MUCH LESS WEIRDLY!
    """"""
    return f"datashuttle/rclone/{password_filepath.stem}"


def set_credentials_as_password_command(password_filepath: Path):
    """"""
    #    if platform.system() == "Windows":
    #        filepath = Path(filepath).resolve()

    if platform.system() == "Windows":
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

    elif platform.system() == "Linux":
        os.environ["RCLONE_PASSWORD_COMMAND"] = (
            f"/usr/bin/pass {name_from_file(password_filepath)}"
        )

    elif platform.system() == "Darwin":
        os.environ["RCLONE_PASSWORD_COMMAND"] = (
            f"/usr/bin/security find-generic-password -a datashuttle -s {name_from_file(password_filepath)} -w"
        )


def set_rclone_password(password_filepath: Path, config_filepath: Path):
    """"""
    if (
        platform.system() == "Windows"
    ):  # TODO: handle this properly, only windows uses a password file.
        assert password_filepath.exists(), (
            "password file not found at point of config creation."
        )

    set_credentials_as_password_command(
        password_filepath
    )  # TODO: OMG handle this

    breakpoint()
    subprocess.run(
        f"rclone config encryption set --config {config_filepath.as_posix()}",
        shell=True,
    )

    remove_credentials_as_password_command()


# TODO: HANDLE ERRORS
def remove_rclone_password(password_filepath: Path, config_filepath: Path):
    """"""
    set_credentials_as_password_command(Path(password_filepath))
    subprocess.run(
        rf"rclone config encryption remove --config {config_filepath.as_posix()}",
        shell=True,
    )

    # TODO: HANDLE ERRORS
    remove_credentials_as_password_command()


def remove_credentials_as_password_command():
    if "RCLONE_PASSWORD_COMMAND" in os.environ:
        os.environ.pop("RCLONE_PASSWORD_COMMAND")
