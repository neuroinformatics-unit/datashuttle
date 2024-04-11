from typing import Any, Literal, Tuple

TopLevelFolder = Literal["rawdata", "derivatives"]

OverwriteExistingFiles = Literal["never", "always", "if_source_newer"]

Prefix = Literal["sub", "ses"]

InterfaceOutput = Tuple[bool, Any]
