import os
import warnings

import pytest
import test_utils

from datashuttle import DataShuttle
from datashuttle.configs.canonical_configs import (
    get_canonical_config_dict,
    get_canonical_config_required_types,
)
from datashuttle.utils import folders

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

        default_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, set_as_defaults=True
        )
        setup_project.make_config_file(**default_configs)

        yield setup_project
        test_utils.teardown_project(cwd, setup_project)

    # -------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------

    # Test Errors
    # -------------------------------------------------------------

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

    def test_no_ssh_options_set_on_make_config_file(self, project):
        """
        Check that program will assert if not all ssh options
        are set on make_config_file
        """
        with pytest.raises(BaseException) as e:
            project.make_config_file(
                project.project_name,
                project.project_name,
                "ssh",
                use_behav=True,
            )

        assert (
            str(e.value)
            == "'central_host_id' and 'central_host_username' are "
            "required if 'connection_method' is 'ssh'."
        )

    @pytest.mark.parametrize(
        "argument_type",
        ["none", "central_host_id", "central_host_username", "both"],
    )
    def test_no_ssh_options_set_update_config(
        self, project, argument_type, tmp_path
    ):
        """
        Check every config option missing does not allow
        switching on ssh_to_central unless all options
        are set.
        """
        project.make_config_file(
            tmp_path / "test_local_path" / project.project_name,
            tmp_path / "test_central_path" / project.project_name,
            "local_filesystem",
            use_behav=True,
        )

        if argument_type in ["central_host_id", "both"]:
            project.update_config("central_host_id", "fake_id")

        if argument_type in ["central_host_username", "both"]:
            project.update_config("central_host_username", "fake_username")

        if argument_type == "both":
            project.update_config("connection_method", "ssh")
            assert project.cfg["connection_method"] == "ssh"
        else:
            with pytest.raises(BaseException) as e:
                project.update_config("connection_method", "ssh")

            assert (
                str(e.value)
                == "\n'central_host_id' and 'central_host_username' are required "
                "if 'connection_method' is 'ssh'.\nconnection_method was not updated."
            )
            assert project.cfg["connection_method"] == "local_filesystem"

    # Test Make Configs API
    # -------------------------------------------------------------

    def test_required_configs(self, project, tmp_path):
        """
        Set the required arguments of the config (local_path, central_path,
        connection_method and check they are set correctly in both
        the project.cfg dict and config.yaml file.
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, required_arguments_only=True
        )

        project.make_config_file(**required_options)

        self.check_config_reopen_and_check_config_again(
            project,
            required_options,
        )

    def test_config_defaults(self, project, tmp_path):
        """
        Check the default configs are set as expected
        (see get_test_config_arguments_dict()) for tested defaults.
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, required_arguments_only=True
        )

        project.make_config_file(**required_options)

        default_options = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, set_as_defaults=True
        )

        test_utils.check_configs(project, default_options)

    def test_non_default_configs(self, project, tmp_path):
        """
        Set the configs to non-default options, make the
        config file and check file and project.cfg are set correctly.
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, set_as_defaults=False
        )

        project.make_config_file(**changed_configs)
        self.check_config_reopen_and_check_config_again(
            project, changed_configs
        )

    # Test Update Configs
    # -------------------------------------------------------------

    def test_update_config(self, project, tmp_path):
        """
        Set the configs as default and then sequentially update
        each entry with a different option. Check that
        the option is updated at project.cfg and the yaml file.
        """
        default_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, set_as_defaults=True
        )

        project.make_config_file(**default_configs)

        not_set_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME, set_as_defaults=False
        )

        test_utils.move_some_keys_to_end_of_dict(not_set_configs)

        for key, value in not_set_configs.items():
            project.update_config(key, value)
            default_configs[key] = value
            test_utils.check_configs(project, default_configs)

    # Test Supplied Configs
    # -------------------------------------------------------------

    def test_supplied_config_file_bad_path(self, setup_project):
        # Test path supplied that doesn't exist

        non_existant_path = setup_project._datashuttle_path / "fake.file"

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(non_existant_path, warn=False)

        assert str(e.value) == f"No file found at: {non_existant_path}."

        # Test non-yaml file supplied
        wrong_filetype_path = setup_project._datashuttle_path / "file.yuml"

        with open(wrong_filetype_path, "w"):
            pass

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(wrong_filetype_path, warn=False)

        assert str(e.value) == "The config file must be a YAML file."

    def test_supplied_config_file_missing_key(self, setup_project, tmp_path):
        """
        More informative traceback is also printed
        """
        bad_configs_path = setup_project._datashuttle_path / "bad_config.yaml"
        missing_key_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME
        )

        del missing_key_configs["use_histology"]

        test_utils.dump_config(missing_key_configs, bad_configs_path)

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(bad_configs_path, warn=False)

        assert (
            str(e.value) == "Loading Failed. "
            "The key 'use_histology' was not found in "
            "the config. Config file was not updated."
        )

    def test_supplied_config_file_extra_key(self, setup_project, tmp_path):
        """
        More informative traceback is also printed
        """
        bad_configs_path = setup_project._datashuttle_path / "bad_config.yaml"

        wrong_key_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME
        )
        wrong_key_configs["use_mismology"] = "wrong"
        test_utils.dump_config(wrong_key_configs, bad_configs_path)

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(bad_configs_path, warn=False)

        assert (
            str(e.value) == "The config contains an "
            "invalid key: use_mismology. "
            "Config file was not updated."
        )

    def test_supplied_config_file_bad_types(self, setup_project, tmp_path):
        """ """
        bad_configs_path = setup_project._datashuttle_path / "bad_config.yaml"

        for key in setup_project.cfg.keys():
            if key in setup_project.cfg.keys_str_on_file_but_path_in_class:
                continue

            bad_type_configs = test_utils.get_test_config_arguments_dict(
                tmp_path, TEST_PROJECT_NAME
            )

            bad_type_configs[key] = DataShuttle  # arbitrary bad type

            test_utils.dump_config(bad_type_configs, bad_configs_path)

            with pytest.raises(BaseException) as e:
                setup_project.supply_config_file(bad_configs_path, warn=False)

            required_types = get_canonical_config_required_types()

            if key == "connection_method":
                assert (
                    str(e.value)
                    == "'<class 'datashuttle.datashuttle.DataShuttle'>' "
                    "not in ('ssh', 'local_filesystem')"
                )
            elif key == "transfer_verbosity":
                assert (
                    str(e.value)
                    == "'<class 'datashuttle.datashuttle.DataShuttle'>' not in ('v', 'vv')"
                )

            else:
                assert (
                    str(e.value) == f"The type of the value at '{key}' is "
                    f"incorrect, it must be {required_types[key]}. "
                    f"Config file was not updated."
                )

    def test_supplied_config_file_changes_wrong_order(
        self, setup_project, tmp_path
    ):
        bad_order_configs_path = (
            setup_project._datashuttle_path / "new_configs.yaml"
        )
        good_order_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME
        )

        bad_order_configs = {
            key: good_order_configs[key]
            for key in reversed(good_order_configs.keys())
        }

        test_utils.dump_config(bad_order_configs, bad_order_configs_path)

        with pytest.raises(BaseException) as e:
            setup_project.supply_config_file(
                bad_order_configs_path, warn=False
            )

        assert (
            str(e.value) == f"New config keys are in the wrong order. "
            f"The order should be: {get_canonical_config_dict().keys()}."
        )

    def test_supplied_config_file_updates(self, setup_project, tmp_path):
        """
        This will check every config.
        """
        (
            new_configs_path,
            new_configs,
        ) = test_utils.make_correct_supply_config_file(setup_project, tmp_path)

        setup_project.supply_config_file(new_configs_path, warn=False)

        test_utils.check_configs(setup_project, new_configs)

    @pytest.mark.parametrize("path_type", ["local_path", "central_path"])
    def test_config_wrong_project_name(self, project, path_type, tmp_path):
        """ """
        bad_name_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, TEST_PROJECT_NAME
        )

        from pathlib import Path

        bad_name = "wrong_project_name"
        bad_name_configs[path_type] = (
            Path(bad_name_configs[path_type]) / bad_name
        )

        with pytest.raises(BaseException) as e:
            project.make_config_file(**bad_name_configs)

        assert (
            f"The {path_type} does not end in the project name: {project.project_name}."
            in str(e.value)
        )

    def test_existing_projects(self, monkeypatch, tmp_path):
        """
        Test existing projects are correctly found based on whether
        they exist in the home directory and contain a config.yaml.

        By default, datashuttle saves project folders to
        Path.home() / .datashuttle. In order to not mess with
        the home directory during this test the `get_datashuttle_path()`
        function is monkeypatched in order to point to a tmp_path.

        The tmp_path / "projects" is filled with a mix of project folders
        with and without config, and tested against accordingly. The `local_path`
        and `central_path` specified in the DataShuttle config are arbitrarily put in
        `tmp_path`.
        """

        def patch_get_datashuttle_path():
            return tmp_path / "projects"

        monkeypatch.setattr(
            "datashuttle.configs.canonical_folders.get_datashuttle_path",
            patch_get_datashuttle_path,
        )

        project_1 = DataShuttle("project_1")
        project_1.make_config_file(
            tmp_path / "project_1",
            tmp_path / "project_1",
            "local_filesystem",
            use_behav=True,
        )

        # project 2 will not be found, because it does not
        # have a config file.
        os.mkdir(tmp_path / "projects" / "project_2")

        project_2 = DataShuttle("project_3")
        project_2.make_config_file(
            tmp_path / "project_3",
            tmp_path / "project_3",
            "local_filesystem",
            use_behav=True,
        )

        (
            project_names,
            project_paths,
        ) = folders.get_existing_project_paths_and_names()

        assert sorted(project_names) == ["project_1", "project_3"]
        assert sorted(project_paths) == [
            (tmp_path / "projects" / "project_1"),
            (tmp_path / "projects" / "project_3"),
        ]

    # --------------------------------------------------------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------------------------------------------------------

    def check_config_reopen_and_check_config_again(
        self, setup_project, *kwargs
    ):
        """
        Check the config file and project.cfg against provided kwargs,
        delete the project and set up the project again,
        checking everything is loaded correctly.
        """
        test_utils.check_configs(setup_project, kwargs[0])

        del setup_project  # del project is almost certainly unnecessary

        setup_project = DataShuttle(TEST_PROJECT_NAME)

        test_utils.check_configs(setup_project, kwargs[0])
