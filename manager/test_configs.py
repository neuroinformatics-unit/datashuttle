import os
import pathlib
import warnings

import pytest
import yaml

from manager import test_utils
from manager.manager import ProjectManager

TEST_PROJECT_NAME = "test_configs"


class TestConfigs:
    """ """

    @pytest.fixture(scope="function")
    def project(test):
        """
        Fixture that creates an empty project. Ignore the warning
        that no configs are setup yet.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        warnings.filterwarnings("ignore")
        project = ProjectManager(TEST_PROJECT_NAME)
        warnings.filterwarnings("default")

        yield project

    # --------------------------------------------------------------------------------------------------------------------
    # Tests
    # --------------------------------------------------------------------------------------------------------------------

    def test_warning_on_startup(self):
        """
        When no configs have been set, a warning should be shown that
        tells the user the config has not been initialized.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        with warnings.catch_warnings(record=True) as w:
            ProjectManager(TEST_PROJECT_NAME)

        assert len(w) == 1
        assert (
            str(w[0].message)
            == "Configuration file has not been initialized. Use make_config_file() to setup before continuing."
        )

    def test_required_configs(self, project):
        """
        Set the required arguemnts of the config (local_path, remote_path,
        ssh_to_remote) and check they are set correctly in both the project.cfg
        dict and config.yaml file.
        """
        required_options = test_utils.get_test_config_arguments_dict(
            required_arguments_only=True
        )

        project.make_config_file(*required_options.values())

        self.check_config_reopen_and_check_config_again(
            project,
            required_options,
        )

    def test_config_defaults(self, project):
        """
        Check the default configs are set as expected
        (see get_test_config_arguments_dict()) for tested defaults.
        """
        required_options = test_utils.get_test_config_arguments_dict(
            required_arguments_only=True
        )

        project.make_config_file(*required_options.values())

        default_options = test_utils.get_test_config_arguments_dict(
            set_as_defaults=True
        )

        self.check_configs(project, default_options)

    def test_non_default_configs(self, project):
        """
        Set the configs to non-default options, make the
        config file and check file and project.cfg are set correctly.
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=False
        )

        project.make_config_file(*changed_configs.values())
        self.check_config_reopen_and_check_config_again(
            project, changed_configs
        )

    def test_update_configs(self, project):
        """
        Set the configs as default and then sequentially update
        each entry with a different option. Check that
        the option is updated at project.cfg and the yaml file.
        """
        default_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=True
        )
        project.make_config_file(*default_configs.values())

        for key, value in {
            "local_path": r"C:/test/test_local/test_edit",
            "remote_path": r"/nfs/testdir/test_edit2",
            "ssh_to_remote": not project.cfg["ssh_to_remote"],
            "remote_host_id": "test_id",
            "remote_host_username": "test_host",
            "sub_prefix": "sub-optional",
            "ses_prefix": "ses-optional",
            "use_ephys": not project.cfg["use_ephys"],
            "use_ephys_behav": not project.cfg["use_ephys_behav"],
            "use_ephys_behav_camera": not project.cfg[
                "use_ephys_behav_camera"
            ],
            "use_behav": not project.cfg["use_behav"],
            "use_behav_camera": not project.cfg["use_behav_camera"],
            "use_histology": not project.cfg["use_histology"],
            "use_imaging": not project.cfg["use_imaging"],
        }.items():

            project.update_config(key, value)
            default_configs[key] = value
            self.check_configs(project, default_configs)

    # --------------------------------------------------------------------------------------------------------------------
    # Test Helpers
    # --------------------------------------------------------------------------------------------------------------------

    def check_configs(
        self,
        project,
        *kwargs,
    ):
        """
        Core function for checking the config against provided configs (kwargs).
        Open the config.yaml file and check the config values stored there,
        and in project.cfg, against the provided configs.

        Paths are stored as pathlib in the cfg but str in the .yaml
        """
        config_path = project.get_appdir_path() + "/config.yaml"

        if not os.path.isfile(config_path):
            raise BaseException("Config file not found.")

        with open(config_path, "r") as config_file:
            config_yaml = yaml.full_load(config_file)

        for arg_name, value in kwargs[0].items():
            if arg_name in ["remote_path", "local_path"]:

                assert type(project.cfg[arg_name]) in [
                    pathlib.PosixPath,
                    pathlib.WindowsPath,
                ]
                assert value == project.cfg[arg_name].as_posix()

            else:
                assert value == project.cfg[arg_name]
                assert value == config_yaml[arg_name]

    # --------------------------------------------------------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------------------------------------------------------

    def check_config_reopen_and_check_config_again(self, project, *kwargs):
        """
        Check the config file and project.cfg against provided kwargs,
        delete the project and setup the project againt,
        checking everything is loaded correctly.
        """
        self.check_configs(project, kwargs[0])

        del project  # del project is almost certainly unecessary

        project = ProjectManager(TEST_PROJECT_NAME)

        self.check_configs(project, kwargs[0])
