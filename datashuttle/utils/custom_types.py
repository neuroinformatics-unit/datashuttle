from __future__ import annotations

from typing import Any, Literal, Tuple

DisplayMode = Literal["error", "warn", "print"]

TopLevelFolder = Literal["rawdata", "derivatives"]

OverwriteExistingFiles = Literal[
    "never", "if_source_newer", "if_different", "always"
]

Prefix = Literal["sub", "ses"]

InterfaceOutput = Tuple[bool, Any]

ConnectionMethods = Literal[
    "ssh", "local_filesystem", "gdrive", "aws", "local_only"
]
