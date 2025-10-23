from typing import Any, Literal, Tuple, TypeAlias, TypedDict

DisplayMode: TypeAlias = Literal["error", "warn", "print"]

TopLevelFolder: TypeAlias = Literal["rawdata", "derivatives"]

OverwriteExistingFiles: TypeAlias = Literal[
    "never", "always", "if_source_newer"
]

Prefix: TypeAlias = Literal["sub", "ses"]

InterfaceOutput: TypeAlias = Tuple[bool, Any]

ConnectionMethods: TypeAlias = Literal[
    "ssh", "local_filesystem", "gdrive", "aws", "local_only"
]


class TransferErrors(TypedDict):
    file_names: list[str]
    messages: list[str]
    nothing_was_transferred_rawdata: bool | None
    nothing_was_transferred_derivatives: bool | None
