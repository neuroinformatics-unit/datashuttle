from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from ..configs.configs import Configs

import copy
import logging
from datetime import datetime
from pathlib import Path

from fancylog import fancylog
from rich import print as rich_print
from rich.console import Console
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree

import datashuttle as package_to_log

from . import utils


def start(
    path_to_log: Path,
    name: str,
    variables: Optional[List[Any]],
    verbose: bool = True,
) -> None:
    """
    Call fancylog to initialise logging.
    """
    filename = get_logging_filename(name)

    fancylog.start_logging(
        path_to_log,
        package_to_log,
        filename=filename,
        variables=variables,
        verbose=verbose,
        timestamp=False,
        file_log_level="DEBUG",
        write_git=True,
        log_to_console=False,
    )
    logging.info(f"Starting logging for command {name}")


def get_logging_filename(name: str) -> str:
    """
    Get the filename to which the log will be saved. This
    starts with ISO8601-formatted datetime, so logs are stored
    in datetime order.
    """
    filename = datetime.now().strftime(f"%Y%m%dT%H%M%S_{name}")
    return filename


def print_tree(project_path: Path) -> None:
    """
    Print a schematic of the folder tree with files
    at project_path to the console.
    """
    tree = get_rich_project_path_tree(project_path)
    rich_print(tree)


def log_tree(project_path: Path) -> None:
    """
    Log a schematic of the folder tree at
    project_path.
    """
    tree_ = get_rich_project_path_tree(project_path)

    console = Console()

    with console.capture() as capture:
        console.print(tree_, markup=True)
    logging.debug(
        capture.get()
    )  # https://github.com/Textualize/rich/issues/2688


def log_names(list_of_headers, list_of_names):
    """
    Log a list of subject or session names.

    Parameters
    ----------

    list_of_headers : a list of titles that the names
    will be printed under, e.g. "sub_names", "ses_names"

    list_of_names : list of names to print to log
    """
    for header, names in zip(list_of_headers, list_of_names):
        utils.log(f"{header}: {names}")


def wrap_variables_for_fancylog(local_vars: dict, cfg: Configs):
    """
    Wrap the locals from the original function call to log
    and the datashuttle.cfg in a wrapper class with __dict__
    attribute for fancylog writing.

    Delete the self attribute (which is DataShuttle class)
    to keep the logs neat, as it adds no information.
    """

    class VariablesState:
        def __init__(self, local_vars_, cfg_):
            local_vars_ = copy.deepcopy(local_vars_)
            del local_vars_["self"]
            self.locals = local_vars_
            self.cfg = copy.deepcopy(cfg_)

    variables = [VariablesState(local_vars, cfg)]

    return variables


# -------------------------------------------------------------------
# File Snapshots
# -------------------------------------------------------------------


def walk_folder(
    project_path: Path, tree: Tree, show_hidden_folders: bool = True
) -> None:
    """
    Demonstrates how to display a tree of files / folders
    with the Tree renderable.

    Based on example from the Rich package.
    https://github.com/Textualize/rich/blob/master/examples/tree.py
    Note the original example contains some other cool
    features (e.g. icons) that were disabled for maximum
    cross-system use.

    Parameters
    ----------

    project_path : path to generate Tree of, usually the
    project local_path

    tree : initialsied rich Tree() class

    show_hidden_folders : Whether hidden folders will be shown in
        the output tree
    """
    paths = sorted(
        project_path.iterdir(),
        key=lambda path: (Path(path).is_file(), path.name.lower()),
    )

    for path in paths:
        # Remove hidden files
        if path.name.startswith(".") and not show_hidden_folders:
            continue
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            branch = tree.add(
                f"[link file://{path}]{escape(path.name)}",
                style=style,
                guide_style=style,
            )
            walk_folder(path, branch)
        else:
            text_filename = Text(path.name, "green")
            #      text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            tree.add(text_filename)


def get_rich_project_path_tree(project_path: Path) -> Tree:
    """
    Get a rich tree class walked through the project_path folder.
    """
    tree = Tree(label=f"{project_path.as_posix()}/")
    walk_folder(project_path, tree)
    return tree


def close_log_filehandler():
    """
    Remove handlers from all loggers.
    """
    logger = logging.getLogger()
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()
