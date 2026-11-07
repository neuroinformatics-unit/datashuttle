from importlib.metadata import PackageNotFoundError, version

from datashuttle.datashuttle_class import DataShuttle
from datashuttle.datashuttle_functions import (
    get_all_sub_and_ses_paths_from_path,
    validate_project_from_path,
)


try:
    __version__ = version("datashuttle")
except PackageNotFoundError:
    # package is not installed
    pass
