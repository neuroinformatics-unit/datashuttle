from __future__ import annotations

from typing import Any, Literal, Tuple, TypedDict

DisplayMode = Literal["error", "warn", "print"]

TopLevelFolder = Literal["rawdata", "derivatives"]

OverwriteExistingFiles = Literal["never", "always", "if_source_newer"]

Prefix = Literal["sub", "ses"]

InterfaceOutput = Tuple[bool, Any]

ConnectionMethods = Literal[
    "ssh", "local_filesystem", "gdrive", "aws", "local_only"
]


class TransferErrors(TypedDict):
    """Type `errors` dictionary (used for collecting `rclone copy` output)."""

    file_names: list[str]
    messages: list[str]
    nothing_was_transferred_rawdata: bool | None
    nothing_was_transferred_derivatives: bool | None
