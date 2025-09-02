import subprocess
import zipfile
from sys import platform

import requests


def get_wezterm_version():
    return "20240203-110809-5046fc22"


def download_wezterm(vendored_dir, wezterm_foldername):
    """ """
    wezterm_url = f"https://github.com/wezterm/wezterm/releases/download/{get_wezterm_version()}/{wezterm_foldername}"  # .zip TODO
    print(wezterm_url)

    wezterm_extracted_dir = vendored_dir / wezterm_foldername
    wezterm_zip_path = vendored_dir / f"{wezterm_foldername}" # .zip"

    # Step 1: Download and extract WezTerm if missing
    if not wezterm_extracted_dir.exists():
        print("⬇ Downloading WezTerm...")
        vendored_dir.mkdir(parents=True, exist_ok=True)
        with requests.get(wezterm_url, stream=True) as response:
            response.raise_for_status()
            with open(wezterm_zip_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)

        print("📦 Extracting WezTerm with system unzip...")

        if platform == "darwin":  ## TODO always use same way
            subprocess.run(
                [
                    "unzip",
                    "-q",
                    str(wezterm_zip_path),
                    "-d",
                    str(vendored_dir),
                ],
                check=True,
            )
        else:
            with zipfile.ZipFile(wezterm_zip_path, "r") as zip_ref:
                zip_ref.extractall(vendored_dir)

        wezterm_zip_path.unlink()  # Optional: clean up ZIP
        print("✅ WezTerm ready.")
    else:
        print("✅ WezTerm already present. Skipping download.")
