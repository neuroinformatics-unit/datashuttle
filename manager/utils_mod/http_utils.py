
# TODO: this is directly copy from https://github.com/brainglobe/bg-atlasapi/blob/5835887c5f9fac16ea1f2682f861411e4f789b3c/bg_atlasapi/utils.py#L132

import configparser
import json
import logging
from typing import Callable

import requests
from rich.panel import Panel
from rich.pretty import Pretty
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.text import Text



def retrieve_over_http(
    url, output_file_path, fn_update: Callable[[int, int], None] = None
):
    """Download file from remote location, with progress bar.
    Parameters
    ----------
    url : str
        Remote URL.
    output_file_path : str or Path
        Full file destination for download.
    fn_update : Callable
        Handler function to update during download. Takes completed and total
        bytes.
    """
    # Make Rich progress bar
    progress = Progress(
        TextColumn("[bold]Downloading...", justify="right"),
        BarColumn(bar_width=None),
        "{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "• speed:",
        TransferSpeedColumn(),
        "• ETA:",
        TimeRemainingColumn(),
    )

    CHUNK_SIZE = 4096
    response = requests.get(url, stream=True)

    try:
        with progress:
            tot = int(response.headers.get("content-length", 0))
            task_id = progress.add_task(
                "download",
                filename=output_file_path.name,
                start=True,
                total=tot,
            )

            with open(output_file_path, "wb") as fout:
                advanced = 0
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    fout.write(chunk)
                    adv = len(chunk)
                    progress.update(task_id, advance=adv, refresh=True)

                    if fn_update:
                        # update handler with completed and total bytes
                        advanced += adv
                        fn_update(advanced, tot)

    except requests.exceptions.ConnectionError:
        output_file_path.unlink()
        raise requests.exceptions.ConnectionError(
            f"Could not download file from {url}"
        )