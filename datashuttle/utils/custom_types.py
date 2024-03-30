from typing import Any, Literal, Tuple

TopLevelFolder = Literal["rawdata", "derivatives"]

Prefix = Literal["sub", "ses"]

InterfaceOutput = Tuple[bool, Any]
