import platform
import subprocess
import zipfile
from pathlib import Path
from sys import platform

import requests


def get_wezterm_version():
    return "20240203-110809-5046fc22"


def download_wezterm(vendored_dir: Path, wezterm_foldername: str) -> None:
    """Download Wezterm for the current platform (macOS or Windows).

    This downloads a specific version of Wezterm, to be vendored in the Datashuttle distribution.
    """
    vendored_dir: str = (
        vendored_dir.as_posix()
    )  # unfortunately we  need to do some Path / str juggling here

    # First set up Wezterm URL and paths depending on platform
    wezterm_url = f"https://github.com/wezterm/wezterm/releases/download/{get_wezterm_version()}/{wezterm_foldername}"
    wezterm_zip_path = f"{vendored_dir}/{wezterm_foldername}"

    if platform.system() == "Windows":
        wezterm_url += ".zip"
        wezterm_zip_path += ".zip"

    wezterm_extracted_dir = f"{vendored_dir}/{wezterm_foldername}"

    # Download and unzip Wezterm (if it has not been downloaded already)
    if Path(wezterm_extracted_dir).exists():
        print(
            f"Not downloading Wezterm as it already exists at {wezterm_extracted_dir}."
        )

    else:
        print(f"Downloading Wezterm from: {wezterm_url}")

        Path(vendored_dir).mkdir(parents=True, exist_ok=True)
        response = requests.get(wezterm_url)
        response.raise_for_status()

        with open(wezterm_zip_path, "wb") as f:
            f.write(response.content)

        print(f"Unzipping Wezterm at: {wezterm_zip_path}")

        if platform == "darwin":
            unzip_macos(wezterm_zip_path, vendored_dir)
        else:
            unzip_windows(wezterm_zip_path, vendored_dir)

        Path(wezterm_zip_path).unlink()


def unzip_macos(wezterm_zip_path: str, vendored_dir: str):
    """Unzip a folder on macOS."""
    subprocess.run(
        [
            "unzip",
            "-q",
            wezterm_zip_path,
            "-d",
            vendored_dir,
        ],
        check=True,
    )


def unzip_windows(wezterm_zip_path: str, vendored_dir: str):
    """Unzip a folder on Windows."""
    with zipfile.ZipFile(wezterm_zip_path, "r") as zip_ref:
        zip_ref.extractall(vendored_dir)
