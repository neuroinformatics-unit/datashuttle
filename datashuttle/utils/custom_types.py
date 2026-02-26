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


class TransferOutput(TypedDict):
    """Type `errors` dictionary (used for collecting `rclone copy` output)."""

    errors: _TransferOutputErrors
    num_files_transferred: _TransferOutputNumFiles


class _TransferOutputErrors:
    file_names: list[str]
    messages: list[str]


class _TransferOutputNumFiles:
    rawdata: int | None
    derivatives: int | None
