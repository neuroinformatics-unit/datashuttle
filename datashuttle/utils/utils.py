from pathlib import Path
from typing import Union

import appdirs

from . import directories

# --------------------------------------------------------------------------------------------------------------------
# General Utils
# --------------------------------------------------------------------------------------------------------------------


def message_user(message: Union[str, list]) -> None:
    """
    Centralised way to send message.
    """
    print(message)


def get_user_input(message: str) -> str:
    """
    Centralised way to get user input
    """
    input_ = input(message)
    return input_


def raise_error(message: str) -> None:
    """
    Temporary centralized way to raise and error
    """
    raise BaseException(message)


def get_appdir_path(project_name: str) -> Path:
    """
    It is not possible to write to program files in windows
    from app without admin permissions. However, if admin
    permission given drag and drop don't work, and it is
    not good practice. Use appdirs module to get the
    AppData cross-platform and save / load all files form here .
    """
    base_path = Path(appdirs.user_data_dir("DataShuttle")) / project_name

    if not base_path.is_dir():
        directories.make_dirs(base_path)

    return base_path


def get_path_after_base_dir(base_dir: Path, path_: Path) -> Path:
    """"""
    if path_already_stars_with_base_dir(base_dir, path_):
        return path_.relative_to(base_dir)
    return path_


def path_already_stars_with_base_dir(base_dir: Path, path_: Path) -> bool:
    return path_.as_posix().startswith(base_dir.as_posix())


def raise_error_not_exists_or_not_yaml(path_to_config: Path) -> None:
    if not path_to_config.exists():
        raise_error(f"No file found at: {path_to_config}")

    if path_to_config.suffix not in [".yaml", ".yml"]:
        raise_error("The config file must be a YAML file")
