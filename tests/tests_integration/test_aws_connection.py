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

        central_path = f"test-datashuttle/test-id-{''.join(random.choices(string.digits, k=15))}"

        aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        aws_access_key_id_secret = os.environ["AWS_ACCESS_KEY_ID_SECRET"]
        aws_region = os.environ["AWS_REGION"]

        no_cfg_project.make_config_file(
            local_path=str(tmp_path),  # any temp location TODO UPDATE
            connection_method="aws",
            central_path=central_path,
            aws_access_key_id=aws_access_key_id,
            aws_region=aws_region,
        )

        state = {"first": True}

        def mock_input(_: str) -> str:
            if state["first"]:
                state["first"] = False
                return "y"
            return aws_access_key_id_secret

        original_input = builtins.input
        builtins.input = mock_input

        no_cfg_project.setup_aws_connection()  # TODO: check that the connection method is correct for these funcs

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
            f"purge central_{no_cfg_project.project_name}_aws:{central_path}"
        )
