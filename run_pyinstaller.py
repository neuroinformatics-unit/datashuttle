import subprocess
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
path_to_spec = f"{dir_path}/windows_spec.spec"
subprocess.call(f"pyinstaller {path_to_spec}")