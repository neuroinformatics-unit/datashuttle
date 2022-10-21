"""
The brainglobe atlas API (BG-AtlasAPI) provides a common interface for programmers to download and process brain atlas data from multiple sources.

https://github.com/brainglobe/bg-atlasapi

BSD 3-Clause License

Copyright (c) 2020, brainglobe
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from typing import Callable

import requests
from rich.progress import (BarColumn, DownloadColumn, Progress, TextColumn,
                           TimeRemainingColumn, TransferSpeedColumn)


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
