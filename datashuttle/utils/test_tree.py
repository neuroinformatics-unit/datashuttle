from rich import get_console
from rich.console import Console
from rich.markup import escape
from rich.tree import Tree
from rich import print as rich_print
from pathlib import Path
from ansimarkup import ansiprint

import logging
from logging import FileHandler

DEBUG = True

path_to_log = r"C:\Users\User\test\log.log"

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[FileHandler(path_to_log, encoding='utf-8')],
)

log = logging.getLogger("rich")

path = Path(r"C:\Users\User\test")  # path to arbitrary folder

tree = Tree(label="Test")
style = "dim" if path.name.startswith("__") else ""
tree.add(
    f"[bold magenta]:open_file_folder: [link file://{path}]{escape(path.name)}",
    style=style,
    guide_style=style,
)

console = get_console()
with console.capture() as capture:
    console.print(tree, markup=True)

if DEBUG:
    breakpoint()
    rich_print(capture.get())
    ansiprint(capture.get())

log.info(capture.get())
