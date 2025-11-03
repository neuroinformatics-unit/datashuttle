import builtins
import copy
import os

from datashuttle import DataShuttle
from datashuttle.utils import gdrive, utils


def setup_project_for_gdrive(project: DataShuttle):
    """Set up a project with configs for Google Drive transfers.

    The connection credentials are fetched from the environment which
    the developer shall set themselves to test locally. In the CI, these
    are set using the github secrets. A random string is added to the
    central path so that the test project paths do not interfere while
    running multiple test instances simultaneously in CI.
    """
    random_string = utils.get_random_string()

    project.update_config_file(
        connection_method="gdrive",
        central_path=f"/{random_string}/{project.project_name}",
        gdrive_client_id=os.environ["GDRIVE_CLIENT_ID"],
        gdrive_root_folder_id=os.environ["GDRIVE_ROOT_FOLDER_ID"],
    )


def setup_gdrive_connection(project: DataShuttle):
    """
    Convenience function to set up the Google Drive connection by
    mocking user input.

    The mock input is triggered twice. First, to deny the presence of
    a browser. Second, to enter a `GDRIVE_CONFIG_TOKEN` needed to set up
    connection without a browser. The credentials are set in the environment
    by the CI. To run tests locally, the developer must set them themselves.
    """
    state = {"first": True}

    def mock_input(_: str) -> str:
        if state["first"]:
            state["first"] = False
            return "n"
        else:
            return os.environ["GDRIVE_CONFIG_TOKEN"]

    original_input = copy.deepcopy(builtins.input)
    builtins.input = mock_input  # type: ignore

    original_get_secret = copy.deepcopy(gdrive.get_client_secret)
    gdrive.get_client_secret = lambda *args, **kwargs: os.environ[
        "GDRIVE_CLIENT_SECRET"
    ]

    project.setup_gdrive_connection()

    builtins.input = original_input
    gdrive.get_client_secret = original_get_secret


def has_gdrive_environment_variables():
    for key in [
        "GDRIVE_CLIENT_ID",
        "GDRIVE_ROOT_FOLDER_ID",
        "GDRIVE_CONFIG_TOKEN",
        "GDRIVE_CLIENT_SECRET",
    ]:
        if key not in os.environ:
            return False

        if os.environ[key].strip() == "":
            return False

    return True
