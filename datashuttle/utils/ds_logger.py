import logging
from pathlib import Path
from typing import Any, List, Optional

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
    fancylog.start_logging(
        path_to_log,
        package_to_log,
        filename=name,
        variables=variables,
        verbose=verbose,
        timestamp=True,
        file_log_level="DEBUG",
        write_git=False,
        log_to_console=False,
    )
    logging.info(f"Starting {name}")


def print_tree(project_path: Path) -> None:
    """
    Print a schematic of the directory tree with files
    at project_path to the console.
    """
    tree = get_rich_project_path_tree(project_path)
    rich_print(tree)


def log_tree(project_path: Path) -> None:
    """
    Log a schematic of the directory tree at
    project_path.
    """
    tree_ = get_rich_project_path_tree(project_path)

    console = Console()

    with console.capture() as capture:
        console.print(tree_, markup=True)
    logging.info(
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


# -------------------------------------------------------------------
# File Snapshots
# -------------------------------------------------------------------


def walk_directory(
    project_path: Path, tree: Tree, show_hidden_folders: bool = True
) -> None:
    """
    Demonstrates how to display a tree of files / directories
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
            walk_directory(path, branch)
        else:
            text_filename = Text(path.name, "green")
            #      text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            tree.add(text_filename)


def get_rich_project_path_tree(project_path: Path) -> Tree:
    """
    Get a rich tree class walked through the project_path directory.
    """
    tree = Tree(label=f"{project_path.as_posix()}/")
    walk_directory(project_path, tree)
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
