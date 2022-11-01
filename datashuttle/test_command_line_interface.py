import os
import pathlib
import warnings
from click.testing import CliRunner
from datashuttle.command_line_interface import entry

import pytest
import yaml

from datashuttle.datashuttle import DataShuttle

TEST_PROJECT_NAME = "test_configs"

class TestCommandLineInterface:

    def test_check(self):
        runner = CliRunner()
        result = runner.invoke(entry,
                               runner.invoke(entry,
                                             [TEST_PROJECT_NAME + " --test"]))

# VARIABLES
# test input arguments are properly read
# test all functionality one
# make_config_file
# update_config
# setup_ssh_connection_to_remote_server
# make_sub_dir
# upload_data
# download_data
# upload_project_dir_or_file
# download_project_dir_or_file


# FUNCTIONALITY
# test input arguments are properly read
# test all functionality one
# make_config_file
# update_config
# setup_ssh_connection_to_remote_server
# make_sub_dir
# upload_data
# download_data
# upload_project_dir_or_file
# download_project_dir_or_file

