from importlib.metadata import PackageNotFoundError, version

from datashuttle.datashuttle import DataShuttle

try:
    __version__ = version("{{datashuttle.package_name}}")
except PackageNotFoundError:
    # package is not installed
    pass
