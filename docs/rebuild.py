import shutil
import subprocess
from pathlib import Path

build_path = Path(__file__).parent / "build"

if build_path.is_dir():
    shutil.rmtree(build_path)

subprocess.run("sphinx-build ./source ./build", shell=True)
