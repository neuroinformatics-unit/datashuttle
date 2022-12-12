import warnings
from pathlib import Path

import pytest
import test_utils
import yaml

from datashuttle.datashuttle import DataShuttle

TEST_PROJECT_NAME = "test_configs"


class TestConfigs:
    @pytest.fixture(scope="function")
    def project(test):
        """
        Fixture that creates an empty project. Ignore the warning
        that no configs are setup yet.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        warnings.filterwarnings("ignore")
        project = DataShuttle(TEST_PROJECT_NAME)
        warnings.filterwarnings("default")

        yield project

    @pytest.fixture(scope="function")
    def setup_project(self, tmp_path):
        """
        Setup a project with default configs to use
        for testing.

        # Note this fixture is a duplicate of project()
        in test_filesystem_transfer.py fixture
        """
        test_project_name = "test_configs"
        setup_project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )
        yield setup_project
        test_utils.teardown_project(cwd, setup_project)

    # --------------------------------------------------------------------------------------------------------------------
    # Tests
    # --------------------------------------------------------------------------------------------------------------------

    def test_warning_on_startup(self):
        """
        When no configs have been set, a warning should be shown that
        the config has not been initialized. Need to download
        Rclone first to ensure input() is not called.
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
        with pytest.raises(BaseException) as e:
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
                    str(w[0].message) == "WARNING: remote_host_id and "
                    "remote_host_username are "
                    "required if ssh_to_remote is True."
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

        project.make_config_file(**required_options)

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

        project.make_config_file(**required_options)

        default_options = test_utils.get_test_config_arguments_dict(
            set_as_defaults=True
        )

        test_utils.check_configs(project, default_options)

    def test_non_default_configs(self, project):
        """
        Set the configs to non-default options, make the
        config file and check file and project.cfg are set correctly.
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=False
        )

        project.make_config_file(**changed_configs)
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

        project.make_config_file(**default_configs)

        not_set_configs = test_utils.get_not_set_config_args(project)
        for key, value in not_set_configs.items():
            project.update_config(key, value)
            default_configs[key] = value

            test_utils.check_configs(project, default_configs)

    def test_supplied_config_file_bad_path(self, project):

        non_existant_path = Path(project.get_appdir_path() + "fake.file")

        with pytest.raises(BaseException) as e:
            project.supply_config_file(non_existant_path, warn=False)

        assert str(e.value) == ""

        wrong_filetype_path = project.get_appdir_path() + "file.yuml"

        with open(wrong_filetype_path, "w"):
            pass

        with pytest.raises(BaseException) as e:
            project.supply_config_file(non_existant_path, warn=False)

        assert str(e.value) == ""

    def dump_config(self, dict_, path_):
        with open(path_, "w") as config_file:
            yaml.dump(dict_, config_file, sort_keys=False)

    def test_supplied_config_file_missing_key(self, setup_project):

        bad_configs_path = setup_project.get_appdir_path() + "/bad_config.yaml"
        missing_key_configs = test_utils.get_test_config_arguments_dict()

        del missing_key_configs["ssh_to_remote"]

        self.dump_config(missing_key_configs, bad_configs_path)

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(bad_configs_path, warn=False)

        assert (
            str(e.value) == "Loading Failed. The key ssh_to_remote was "
            "not found in the supplied config. Config "
            "file was not updated."
        )

    def test_supplied_config_file_extra_key(self, setup_project):

        bad_configs_path = setup_project.get_appdir_path() + "/bad_config.yaml"

        wrong_key_configs = test_utils.get_test_config_arguments_dict()
        wrong_key_configs["use_mismology"] = "wrong"
        self.dump_config(wrong_key_configs, bad_configs_path)

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(bad_configs_path, warn=False)

        assert (
            str(e.value) == "Loading Failed. The key sub_prefix was not "
            "found in the supplied config. "
            "Config file was not updated."
        )

    def test_supplied_config_file_bad_types(self, setup_project):
        """ """
        bad_configs_path = setup_project.get_appdir_path() + "/bad_config.yaml"

        for key in setup_project.cfg.keys():
            if key in setup_project.cfg.keys_str_on_file_but_path_in_class:
                continue

            bad_type_configs = test_utils.get_test_config_arguments_dict()

            bad_type_configs[key] = DataShuttle

            self.dump_config(bad_type_configs, bad_configs_path)

            with pytest.raises(BaseException) as e:
                setup_project.supply_config_file(bad_configs_path, warn=False)

            try:
                assert f"The type of the value at {key} is incorrect" in str(
                    e.value
                )
            except:
                breakpoint()

    # need to move sub / ses from config dict to config class.
    # then can move sub
    # then this should work

    def test_supplied_config_file_updates(self, setup_project):
        """
        This will check everything
        """
        new_configs_path = (
            setup_project.get_appdir_path() + "/new_configs.yaml"
        )
        new_configs = test_utils.get_test_config_arguments_dict()

        new_configs["local_path"] = "new_fake_local"
        new_configs["remote_path_local"] = "new_fake_remote_local"
        new_configs["remote_path_ssh"] = "new_fake_remote_ssh"

        self.dump_config(new_configs, new_configs_path)

        setup_project.supply_config_file(new_configs_path, warn=False)

        test_utils.check_configs(setup_project, new_configs)

    def test_supplied_config_file_changes_wrong_order(self, setup_project):

        bad_order_configs_path = (
            setup_project.get_appdir_path() + "/new_configs.yaml"
        )
        good_order_configs = test_utils.get_test_config_arguments_dict()

        bad_order_configs = dict(reversed(good_order_configs))

        self.dump_config(bad_order_configs, bad_order_configs_path)

        setup_project.supply_config_file(bad_order_configs_path, warn=False)

        with pytest.raises(BaseException):
            test_utils.check_configs(setup_project, bad_order_configs)

        test_utils.check_configs(setup_project, good_order_configs)

    # --------------------------------------------------------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------------------------------------------------------

    def check_config_reopen_and_check_config_again(
        self, setup_project, *kwargs
    ):
        """
        Check the config file and project.cfg against provided kwargs,
        delete the project and setup the project againt,
        checking everything is loaded correctly.
        """
        test_utils.check_configs(setup_project, kwargs[0])

        del setup_project  # del project is almost certainly unecessary

        setup_project = DataShuttle(TEST_PROJECT_NAME)

        test_utils.check_configs(setup_project, kwargs[0])
