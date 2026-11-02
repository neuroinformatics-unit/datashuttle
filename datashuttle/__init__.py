from importlib.metadata import PackageNotFoundError, version

from datashuttle.datashuttle_class import DataShuttle
from datashuttle.datashuttle_functions import (
    delete_expired_trash,
    delete_project_from_disk,
    empty_trash,
    get_deleted_projects,
    restore_project_from_trash,
    validate_project_from_path,
)


try:
    __version__ = version("datashuttle")
except PackageNotFoundError:
    # package is not installed
    pass
