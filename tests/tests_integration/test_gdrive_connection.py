import builtins
import os
import random
import string

import pytest
import test_utils
from base import BaseTest

from datashuttle.configs.canonical_configs import get_broad_datatypes
from datashuttle.utils import rclone


@pytest.mark.skipif(os.getenv("CI") is None, reason="Only runs in CI")
class TestGoogleDriveGithubCI(BaseTest):

    def test_google_drive_connection(self, no_cfg_project, tmp_path):

        central_path = (
            f"test-id-{''.join(random.choices(string.digits, k=15))}"
        )

        root_id = os.environ["GDRIVE_ROOT_FOLDER_ID"]
        sa_path = os.environ["GDRIVE_SERVICE_ACCOUNT_FILE"]

        no_cfg_project.make_config_file(
            local_path=str(tmp_path),  # any temp location TODO UPDATE
            connection_method="gdrive",
            central_path=central_path,
            gdrive_root_folder_id=root_id,
            gdrive_client_id=None,  # keep None
        )

        state = {"first": True}

        def mock_input(_: str) -> str:
            if state["first"]:
                state["first"] = False
                return "n"
            return sa_path

        original_input = builtins.input
        builtins.input = mock_input

        no_cfg_project.setup_google_drive_connection()

        builtins.input = original_input

        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project_folders(
            no_cfg_project, "rawdata", subs, sessions, get_broad_datatypes()
        )

        no_cfg_project.upload_entire_project()

        # get a list of files on gdrive and check they are as expected
        # assert the test id if its failed

        # only tidy up if as expected, otherwise we can leave the folder there to have a look
        # and delete manually later
        rclone.call_rclone(
            f"purge central_{no_cfg_project.project_name}_gdrive:{central_path}"
        )
