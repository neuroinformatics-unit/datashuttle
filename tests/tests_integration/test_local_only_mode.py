import os.path
import shutil

import pytest
from base import BaseTest

from datashuttle.utils import formatting, validation
from datashuttle.utils.custom_exceptions import NeuroBlueprintError, ConfigError
from datashuttle import DataShuttle
import test_utils

TEST_PROJECT_NAME = "test_project"  # TODO: centralise


class TestLocalOnlyMode(BaseTest):

    @pytest.fixture(scope="function")
    def local_project(self, tmp_path):
        """
        """
        tmp_path = tmp_path / "test_local"

        project = DataShuttle(TEST_PROJECT_NAME)
        project.make_config_file(local_path=tmp_path)

        cwd = os.getcwd()
        yield project
        test_utils.teardown_project(cwd, project)

    def test_bad_setup(self, tmp_path):
        """
        """
        local_path = tmp_path / "test_local"  # TODO

        project = DataShuttle(TEST_PROJECT_NAME)

        with pytest.raises(ConfigError) as e:
            project.make_config_file(local_path, central_path=tmp_path / "central")
        assert "Either both `central_path` and `connection_method` must be set" in str(e.value)

        with pytest.raises(ConfigError) as e:
            project.make_config_file(local_path, connection_method="ssh")
        assert "Either both `central_path` and `connection_method` must be set" in str(e.value)


    def test_full_to_local_project(self, project):
        """
        """
        project.update_config_file(central_path=None, connection_method=None)

        with pytest.raises(ConfigError) as e:
            project.upload_entire_project()

        assert "This function cannot be used for a local-project." in str(e.value)

        project.create_folders("rawdata", "sub-001", "ses-001", "ephys")

        project.validate_project("rawdata", "error")

    def test_local_to_full_project(self, local_project):
        """
        """
        central_path = local_project.cfg["local_path"].parent / "central"

        local_project.update_config_file(central_path=central_path, connection_method="local_filesystem")

        paths_ = local_project.create_folders("rawdata", "sub-001", "ses-001", "ephys")
        test_utils.write_file(paths_["ephys"][0] / "test_file", contents="test_entry")

        local_project.validate_project("rawdata", "error")

        local_project.upload_entire_project()

        assert (central_path / TEST_PROJECT_NAME / "rawdata" / "sub-001" / "ses-001" / "ephys" / "test_file").is_file()


    # test setup and make configs with bad configs

    # test full to restricted

    # test restricted to full

    # test create and validate

    # test get next sub

