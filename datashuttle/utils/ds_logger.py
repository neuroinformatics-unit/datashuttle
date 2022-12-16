import logging
from pathlib import Path

import fancylog as package
from fancylog import fancylog
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree
from typimg import Any, Optional


def start(
    path_to_log: Path, name: str, variables: Optional[list[Any]]
) -> None:
    """"""
    fancylog.start_logging(
        path_to_log,
        package,
        filename=name,
        variables=variables,
        verbose=False,
        timestamp=True,
        file_log_level="INFO",
        write_git=False,
    )
    logging.info(f"Starting {name}")


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
    """
    paths = sorted(
        project_path.iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
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
            text_filename.stylize(f"[link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(
                f" ({decimal(file_size)})", "blue"
            )  # TODO: these might be hard to see on dark background
            tree.add(text_filename)


def get_rich_project_path_tree(project_path: Path) -> Tree:
    """ """
    tree = Tree(label="Project Folder Snapshot")
    walk_directory(project_path, tree)
    return tree
