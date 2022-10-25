import os
import pathlib
import warnings

import pytest
import yaml

from datashuttle.datashuttle.datashuttle import DataShuttle
from datashuttle.tests import test_utils

TEST_PROJECT_NAME = "test_configs"


class TestConfigs:
    @pytest.fixture(scope="function")
    def project(test):
        """
        Fixture that creates an empty project. Ignore the warning
        that no configs are setup yet.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        test_utils.check_and_download_rclone()

        warnings.filterwarnings("ignore")
        project = DataShuttle(TEST_PROJECT_NAME)
        warnings.filterwarnings("default")

        yield project

    # --------------------------------------------------------------------------------------------------------------------
    # Tests
    # --------------------------------------------------------------------------------------------------------------------

    def test_warning_on_startup(self):
        """
        When no configs have been set, a warning should be shown that
        the config has not been initialized.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        with pytest.warns() as w:
            DataShuttle(TEST_PROJECT_NAME)

        assert len(w) == 1
        assert (
            str(w[0].message)
            == "Configuration file has not been initialized. "
            "Use make_config_file() to setup before continuing."
        )

    def test_fail_to_pass_remote_path(self, project):
        """
        Test that the make_config_file will assert if neither
        remote_path_ssh or remote_path_local are passed.
        """
        with pytest.raises(AssertionError) as e:
            project.make_config_file("test_local_path", False)

        assert (
            str(e.value)
            == "Must set either remote_path_ssh or remote_path_local"
        )

    def test_no_remote_local_path_set(self, project):
        """
        Check that if the local path is not set and
        then tries to turn off ssh_to_remote, it will
        warn that the setting was not updated.
        """
        project.make_config_file(
            "test_local_path",
            True,
            remote_path_ssh="random_path",
            remote_host_id="fake_id",
            remote_host_username="fake_user",
        )

        with pytest.warns() as w:
            project.update_config("ssh_to_remote", False)

        assert len(w) == 2

        assert (
            str(w[0].message) == "WARNING: ssh to remote is off but "
            "remote_path_local has not been set."
        )

        assert str(w[1].message) == "ssh_to_remote was not updated"

        assert project.cfg["ssh_to_remote"] is True

    def test_no_ssh_options_set_on_make_config_file(self, project):
        """
        Check that program will assert if not all ssh options
        are set on make_config_file
        """
        with pytest.raises(
            BaseException
        ) as e:  # TODO: checkk what the original exceptions were
            project.make_config_file(
                "test_local_path", True, remote_path_local="local_path"
            )

        assert (
            str(e.value)
            == "ssh to remote is on but remote_path_ssh has not been set."
        )

    @pytest.mark.parametrize(
        "argument_type",
        ["none", "remote_host_id", "remote_host_username", "both"],
    )
    def test_no_ssh_options_set_update_config(self, project, argument_type):
        """
        Check every config option missing does not allow
        switching on ssh_to_remote unless all options
        are set.
        """
        project.make_config_file(
            "test_local_path",
            False,
            remote_path_local="local_path",
            remote_path_ssh="ssh_path",
        )

        if argument_type in ["remote_host_id", "both"]:
            project.update_config("remote_host_id", "fake_id")

        if argument_type in ["remote_host_username", "both"]:
            project.update_config("remote_host_username", "fake_username")

        with warnings.catch_warnings(record=True) as w:
            project.update_config("ssh_to_remote", True)

            if argument_type == "both":
                assert len(w) == 0
                assert project.cfg["ssh_to_remote"] is True
            else:
                assert len(w) == 2

                assert (
                    str(w[0].message)
                    == "WARNING: ssh to remote set but no remote_host_id "
                    "or remote_host_username not provided."
                )

                assert str(w[1].message) == "ssh_to_remote was not updated"

                assert project.cfg["ssh_to_remote"] is False

    def test_required_configs(self, project):
        """
        Set the required arguments of the config (local_path, ssh_to_remote,
        remote_path_ssh, remote_path_local (at least one of the last 2 are
        required so both input) and check they are set correctly in both
        the project.cfg dict and config.yaml file.
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
            "remote_path_local": r"/nfs/testdir/test_edit2",
            "remote_path_ssh": r"/nfs/testdir/test_edit3",
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
            "ssh_to_remote": not project.cfg[
                "ssh_to_remote"
            ],  # test last so ssh items already set
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
        Core function for checking the config against
        provided configs (kwargs). Open the config.yaml file
        and check the config values stored there,
        and in project.cfg, against the provided configs.

        Paths are stored as pathlib in the cfg but str in the .yaml
        """
        config_path = project.get_appdir_path() + "/config.yaml"

        if not os.path.isfile(config_path):
            raise BaseException("Config file not found.")

        with open(config_path, "r") as config_file:
            config_yaml = yaml.full_load(config_file)

        for arg_name, value in kwargs[0].items():

            if arg_name in [
                "local_path",
                "remote_path_ssh",
                "remote_path_local",
            ]:
                assert type(project.cfg[arg_name]) in [
                    pathlib.PosixPath,
                    pathlib.WindowsPath,
                ]
                assert value == project.cfg[arg_name].as_posix()

            else:
                assert value == project.cfg[arg_name], f"{arg_name}"
                assert value == config_yaml[arg_name], f"{arg_name}"

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

        project = DataShuttle(TEST_PROJECT_NAME)

        self.check_configs(project, kwargs[0])
