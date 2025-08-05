import builtins
import copy
import os
import random
import string

from datashuttle import DataShuttle
from datashuttle.utils import gdrive


def setup_project_for_gdrive(project: DataShuttle):
    """
    Set up a project with configs for Google Drive transfers.
    """
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choices(characters, k=15))

    project.update_config_file(
        connection_method="gdrive",
        central_path=f"/main/{random_string}/{project.project_name}",
        gdrive_client_id=os.environ["GDRIVE_CLIENT_ID"],
        gdrive_root_folder_id=os.environ["GDRIVE_ROOT_FOLDER_ID"],
    )


def setup_gdrive_connection(project: DataShuttle):
    """
    Convenience function to set up the Google Drive connection by
    mocking user input.
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

    project.setup_google_drive_connection()

    builtins.input = original_input
    gdrive.get_client_secret = original_get_secret
