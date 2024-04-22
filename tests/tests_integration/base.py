import os
import platform
import subprocess
import subprocess

import warnings

import pytest
import ssh_test_utils
import test_utils

from datashuttle import DataShuttle

TEST_PROJECT_NAME = "test_project"


class BaseTest:

    @pytest.fixture(scope="function")
    def no_cfg_project(test):
        """
        Fixture that creates an empty project. Ignore the warning
        that no configs are setup yet.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        warnings.filterwarnings("ignore")
        no_cfg_project = DataShuttle(TEST_PROJECT_NAME)
        warnings.filterwarnings("default")

        yield no_cfg_project

    @pytest.fixture(scope="function")
    def project(self, tmp_path, request):
        """
        Set up a project with default configs to use for testing.

        This fixture uses indirect parameterization to test both 'full'
        and 'local-only' (no `central_path` or `connection_method`). The
        decorator:

        `@pytest.mark.parametrize("project", ["local", "full"], indirect=True)`

        will call this function twice, with "local" or "full" in the request.param
        field (below, if not passed the default is set to "full"). Depending
        on the parameter, set up a project in full or local-only mode.
        """
        tmp_path = tmp_path / "test with space"

        project_type = getattr(request, "param", "full")

        if project_type == "full":
            project = test_utils.setup_project_default_configs(
                TEST_PROJECT_NAME,
                tmp_path,
                local_path=tmp_path / TEST_PROJECT_NAME,
            )
        elif project_type == "local":
            test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)
            project = DataShuttle(TEST_PROJECT_NAME)
            project.make_config_file(local_path=tmp_path / TEST_PROJECT_NAME)

        else:
            raise ValueError("`parametrized value must be 'full' or 'local'")

        yield project
        test_utils.teardown_project(project)

    @pytest.fixture(scope="function")
    def clean_project_name(self):
        """
        Create an empty project, but ensure no
        configs already exists, and delete created configs
        after test.
        """
        project_name = TEST_PROJECT_NAME
        test_utils.delete_project_if_it_exists(project_name)
        yield project_name
        test_utils.delete_project_if_it_exists(project_name)

    @pytest.fixture(
        scope="session",
    )
    def setup_ssh_container(self):
        # Annoying session scope does not seem to actually work
        container_name = "running_ssh_tests"
        ssh_test_utils.setup_ssh_container(container_name)
        yield
        subprocess.run(f"docker stop {container_name}", shell=True)
        subprocess.run(f"docker rm {container_name}", shell=True)
