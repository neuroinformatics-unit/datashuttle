<<<<<<< HEAD
=======
import os
import platform
import subprocess
>>>>>>> 75d3f43 (Try build and run docker only once per session.)
import warnings
from pathlib import Path

import pytest
import ssh_test_utils
import test_utils
from file_conflicts_pathtable import get_pathtable

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
        no_cfg_project = test_utils.make_project(TEST_PROJECT_NAME)
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
            project = test_utils.make_project(TEST_PROJECT_NAME)
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
        scope="class",
    )
    def pathtable_and_project(self, tmpdir_factory):
        """
        Create a new test project with a test project folder
        and file structure (see `get_pathtable()` for definition).
        """
        tmp_path = tmpdir_factory.mktemp("test")

        base_path = tmp_path / "test with space"
        test_project_name = "test_file_conflicts"

        project, cwd = test_utils.setup_project_fixture(
            base_path, test_project_name
        )

        pathtable = get_pathtable(project.cfg["local_path"])

        self.create_all_pathtable_files(pathtable)

        yield [pathtable, project]

        test_utils.teardown_project(cwd, project)

    @pytest.fixture(
        scope="session",
    )
    def setup_ssh_container(self):
        """"""
        PORT = 3306  # https://github.com/orgs/community/discussions/25550
        os.environ["DS_SSH_PORT"] = str(PORT)

        assert ssh_test_utils.docker_is_running(), (
            "docker is not running, "
            "this should be checked at the top of test script"
        )

        image_path = Path(__file__).parent.parent / "ssh_test_images"
        os.chdir(image_path)

        if platform.system() == "Linux":
            build_command = "sudo docker build -t ssh_server ."
            run_command = f"sudo docker run -d -p {PORT}:22 ssh_server"
        else:
            build_command = "docker build ."
            run_command = f"docker run -d -p {PORT}:22 ssh_server"

        build_output = subprocess.run(
            build_command,
            shell=True,
            capture_output=True,
        )
        assert build_output.returncode == 0, (
            f"docker build failed with: STDOUT-{build_output.stdout} STDERR-"
            f"{build_output.stderr}"
        )

        run_output = subprocess.run(
            run_command,
            shell=True,
            capture_output=True,
        )

        assert run_output.returncode == 0, (
            f"docker run failed with: STDOUT-{run_output.stdout} STDE"
            f"RR-{run_output.stderr}"
        )

    #   setup_project_for_ssh(
    #      project,
    #     central_path=f"/home/sshuser/datashuttle/{project.project_name}",
    #    central_host_id="localhost",
    #     central_host_username="sshuser",
    # )

    @pytest.fixture(
        scope="class",
    )
    def ssh_setup(self, pathtable_and_project, setup_ssh_container):
        """
        After initial project setup (in `pathtable_and_project`)
        setup a container and the project's SSH connection to the container.
        Then upload the test project to the `central_path`.
        """
        pathtable, project = pathtable_and_project

        ssh_test_utils.setup_project_for_ssh(
            project,
            central_path=f"/home/sshuser/datashuttle/{project.project_name}",
            central_host_id="localhost",
            central_host_username="sshuser",
        )

        # ssh_test_utils.setup_project_and_container_for_ssh(project)
        ssh_test_utils.setup_ssh_connection(project)

        project.upload_rawdata()

        return [pathtable, project]
