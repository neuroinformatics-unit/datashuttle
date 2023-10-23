from importlib.metadata import PackageNotFoundError, version

from datashuttle.datashuttle import DataShuttle

try:
    __version__ = version("datashuttle")
except PackageNotFoundError:
    # package is not installed
    pass
