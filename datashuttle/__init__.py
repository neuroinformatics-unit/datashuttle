from importlib.metadata import PackageNotFoundError, version

from datashuttle.datashuttle_class import DataShuttle
from datashuttle.datashuttle_functions import validate_project_from_path


try:
    __version__ = version("datashuttle")
except PackageNotFoundError:
    # package is not installed
    pass


def get_datashuttle_version():
    return __version__
