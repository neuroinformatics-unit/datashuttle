import os
from pathlib import Path

import pytest
import test_utils
from base import BaseTest

from datashuttle import DataShuttle
from datashuttle.configs.canonical_configs import (
    get_canonical_configs,
)
from datashuttle.utils import getters
from datashuttle.utils.custom_exceptions import ConfigError


class TestConfigs(BaseTest):
    # Test Errors
    # -------------------------------------------------------------

    @pytest.fixture(scope="function")
    def non_existent_path(self, tmp_path):
        """
        Return a path that does not exist.
        """
        non_existent_path = tmp_path / "does_not_exist"
        assert not non_existent_path.is_dir()
        return non_existent_path

    @pytest.fixture(scope="function")
    def existent_path(self, tmp_path):
        """
        Return a path that exists.
        """
        existent_path = tmp_path / "exists"
        os.makedirs(existent_path, exist_ok=True)
        return existent_path

    def test_warning_on_startup(self, no_cfg_project):
        """
        When no configs have been set, a warning should be shown that
        the config has not been initialized. Need to download
        Rclone first to ensure input() is not called.
        """
        project_name = no_cfg_project.project_name
        test_utils.delete_project_if_it_exists(project_name)

        with pytest.warns() as w:
            DataShuttle(project_name)

        assert len(w) == 1
        assert (
            str(w[0].message)
            == "Configuration file has not been initialized. "
            "Use make_config_file() to setup before continuing."
        )

    @pytest.mark.parametrize(
        "bad_pattern",
        [
            "~/my/path",
            ".",
            "../my/path",
        ],
    )
    @pytest.mark.parametrize("path_type", ["local_path", "central_path"])
    def test_bad_path_syntax(self, project, bad_pattern, path_type, tmp_path):
        """
        "~", "." and "../" syntax is not supported because
        it does not work with rclone. Theoretically it
        could be supported by checking for "." etc. and
        filling in manually, but it does not seem robust.

        Here check an error is raised when path contains
        incorrect syntax.

        Note pathlib strips "./" so not checked.
        """
        if bad_pattern != ".":
            bad_pattern = f"{bad_pattern}/{project.project_name}"
        good_pattern = f"{tmp_path}/my/path/{project.project_name}"

        if path_type == "local_path":
            local_path = bad_pattern
            central_path = good_pattern
        else:
            local_path = good_pattern
            central_path = bad_pattern

        os.makedirs(local_path, exist_ok=True)
        os.makedirs(central_path, exist_ok=True)

        with pytest.raises(ConfigError) as e:
            project.make_config_file(
                local_path,
                central_path,
                "local_filesystem",
            )

        assert "must contain the full folder path with no " in str(e.value)

    @pytest.mark.parametrize("path_type", ["local_path", "central_path"])
    def test_non_existant_local_path(
        self, no_cfg_project, path_type, non_existent_path, existent_path
    ):
        """
        Check that if the `local_path` and `central_path` that holds the
        project root does not exist when passed to configs, that an error
        is raised. Note that this error is only raised for `central_path`
        if `connection_method` is `"local_filesystem"`.
        See `test_additional_error_text_when_ssh_used()` for when ssh is used.
        """
        if path_type == "local_path":
            local_path = non_existent_path
            central_path = existent_path
        else:
            local_path = existent_path
            central_path = non_existent_path

        with pytest.raises(BaseException) as e:
            no_cfg_project.make_config_file(
                local_path / no_cfg_project.project_name,
                central_path / no_cfg_project.project_name,
                "local_filesystem",
            )

        assert f"The {path_type}: {non_existent_path} that the project" in str(
            e.value
        )

    def test_additional_error_text_when_ssh_used(
        self, no_cfg_project, non_existent_path, existent_path
    ):
        """
        If SSH is used as `connection_method`, if `local_path` does not exist
        an extra message is printed to warn to check the `central_path`, because
        it cannot be checked.

        Currently if SSH is used and the central path does not exist,
        no error is raised because it is not possible to check.
        """
        with pytest.raises(BaseException) as e:
            no_cfg_project.make_config_file(
                non_existent_path / no_cfg_project.project_name,
                existent_path / no_cfg_project.project_name,
                "ssh",
                central_host_id="fake_id",
                central_host_username="fake_username",
            )

        assert (
            "Also make sure the central_path` is correct, as datashuttle "
            "cannot check it via SSH at this stage." in str(e.value)
        )

        # This should not raise an error, even though the path does not
        # exist, because it is not possible to check over SSH.
        no_cfg_project.make_config_file(
            existent_path / no_cfg_project.project_name,
            non_existent_path / no_cfg_project.project_name,
            "ssh",
            central_host_id="fake_id",
            central_host_username="fake_username",
        )

    def test_no_ssh_options_set_on_make_config_file(self, no_cfg_project):
        """
        Check that program will assert if not all ssh options
        are set on make_config_file
        """
        with pytest.raises(ConfigError) as e:
            no_cfg_project.make_config_file(
                no_cfg_project.project_name,
                no_cfg_project.project_name,
                "ssh",
            )

        assert (
            str(e.value)
            == "'central_host_id' and 'central_host_username' are "
            "required if 'connection_method' is 'ssh'."
        )

    # Test Make Configs API
    # -------------------------------------------------------------

    def test_required_configs(self, no_cfg_project, tmp_path):
        """
        Set the required arguments of the config (local_path, central_path,
        connection_method and check they are set correctly in both
        the no_cfg_project.cfg dict and config.yaml file.
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, no_cfg_project.project_name, required_arguments_only=True
        )

        no_cfg_project.make_config_file(**required_options)

        self.check_config_reopen_and_check_config_again(
            no_cfg_project,
            required_options,
        )

    def test_config_defaults(self, no_cfg_project, tmp_path):
        """
        Check the default configs are set as expected
        (see get_test_config_arguments_dict()) for tested defaults.
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, no_cfg_project.project_name, required_arguments_only=True
        )

        no_cfg_project.make_config_file(**required_options)

        default_options = test_utils.get_test_config_arguments_dict(
            tmp_path, no_cfg_project.project_name, set_as_defaults=True
        )

        test_utils.check_configs(no_cfg_project, default_options)

    def test_non_default_configs(self, no_cfg_project, tmp_path):
        """
        Set the configs to non-default options, make the
        config file and check file and no_cfg_project.cfg are set correctly.
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, no_cfg_project.project_name, set_as_defaults=False
        )

        no_cfg_project.make_config_file(**changed_configs)
        self.check_config_reopen_and_check_config_again(
            no_cfg_project, changed_configs
        )

    # Test Update Config File
    # -------------------------------------------------------------

    def test_update_config_file__(self, no_cfg_project, tmp_path):
        """
        Set the configs as default, and then update them to
        new configs and check they are updated properly.

        Then, update only a subset (back to the defaults) and
        check only the subset is updated.
        """
        default_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, no_cfg_project.project_name, set_as_defaults=True
        )

        no_cfg_project.make_config_file(**default_configs)
        project = no_cfg_project

        not_set_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, project.project_name, set_as_defaults=False
        )

        test_utils.move_some_keys_to_end_of_dict(not_set_configs)

        # ensure Path is converted to str
        not_set_configs["local_path"] = str(not_set_configs["local_path"])

        project.update_config_file(**not_set_configs)

        test_utils.check_configs(project, not_set_configs)

        # Now update only a subset and check only this subset is updated.
        keys_to_not_update = [
            "local_path",
            "connection_method",
            "central_host_id",
            "central_host_username",
            "transfer_verbosity",
        ]

        for key in keys_to_not_update:
            default_configs.pop(key)

        project.update_config_file(**default_configs)

        for key in keys_to_not_update:
            default_configs[key] = not_set_configs[key]

        test_utils.check_configs(project, default_configs)

    # Test Supplied Configs
    # -------------------------------------------------------------

    def test_supplied_config_file_bad_path(self, project):
        # Test path supplied that doesn't exist

        non_existent_path = project._datashuttle_path / "fake.file"

        with pytest.raises(FileNotFoundError) as e:
            project.supply_config_file(non_existent_path, warn=False)

        assert str(e.value) == f"No file found at: {non_existent_path}."

        # Test non-yaml file supplied
        wrong_filetype_path = project._datashuttle_path / "file.yuml"

        with open(wrong_filetype_path, "w"):
            pass

        with pytest.raises(ValueError) as e:
            project.supply_config_file(wrong_filetype_path, warn=False)

        assert str(e.value) == "The config file must be a YAML file."

    def test_supplied_config_file_missing_key(self, project, tmp_path):
        """
        More informative traceback is also printed
        """
        bad_configs_path = project._datashuttle_path / "bad_config.yaml"
        missing_key_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, project.project_name
        )

        del missing_key_configs["transfer_verbosity"]

        test_utils.dump_config(missing_key_configs, bad_configs_path)

        with pytest.raises(ConfigError) as e:
            project.supply_config_file(bad_configs_path, warn=False)

        assert (
            str(e.value) == "Loading Failed. "
            "The key 'transfer_verbosity' was not found in "
            "the config. Config file was not updated."
        )

    def test_supplied_config_file_extra_key(self, project, tmp_path):
        """
        More informative traceback is also printed
        """
        bad_configs_path = project._datashuttle_path / "bad_config.yaml"

        wrong_key_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, project.project_name
        )
        wrong_key_configs["transfer_merbosity"] = "wrong"
        test_utils.dump_config(wrong_key_configs, bad_configs_path)

        with pytest.raises(ConfigError) as e:
            project.supply_config_file(bad_configs_path, warn=False)

        assert (
            str(e.value) == "The config contains an "
            "invalid key: transfer_merbosity. "
            "Config file was not updated."
        )

    def test_supplied_config_file_bad_types(self, project, tmp_path):
        """
        Test the situation when configs with incorrect types are passed
        in a supplied config.
        """
        bad_configs_path = project._datashuttle_path / "bad_config.yaml"

        for key in project.cfg.keys():
            if key in project.cfg.keys_str_on_file_but_path_in_class:
                continue

            bad_type_configs = test_utils.get_test_config_arguments_dict(
                tmp_path, project.project_name
            )

            bad_type_configs[key] = DataShuttle  # arbitrary bad type

            test_utils.dump_config(bad_type_configs, bad_configs_path)

            with pytest.raises(ConfigError) as e:
                project.supply_config_file(bad_configs_path, warn=False)

            required_types = get_canonical_configs()

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

    def test_supplied_config_file_changes_wrong_order(self, project, tmp_path):
        """
        Test the situation when a config file is passed with variables in
        the wrong order.

        TODO: why should this matter? They should be able to be in
        any order and just converted to dict?
        """
        bad_order_configs_path = project._datashuttle_path / "new_configs.yaml"

        good_order_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, project.project_name
        )

        bad_order_configs = {
            key: good_order_configs[key]
            for key in reversed(good_order_configs.keys())
        }

        test_utils.dump_config(bad_order_configs, bad_order_configs_path)

        with pytest.raises(ConfigError) as e:
            project.supply_config_file(bad_order_configs_path, warn=False)

        assert (
            str(e.value) == f"New config keys are in the wrong order. "
            f"The order should be: {get_canonical_configs().keys()}."
        )

    def test_supplied_config_file_updates(self, project, tmp_path):
        """
        This will check every config.
        """
        (
            new_configs_path,
            new_configs,
        ) = test_utils.make_correct_supply_config_file(project, tmp_path)

        project.supply_config_file(new_configs_path, warn=False)

        test_utils.check_configs(project, new_configs)

    @pytest.mark.parametrize("path_type", ["local_path", "central_path"])
    def test_config_wrong_project_name(
        self, no_cfg_project, path_type, tmp_path
    ):
        """ """
        bad_name_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, no_cfg_project.project_name
        )

        bad_name = "wrong_project_name"
        bad_name_configs[path_type] = (
            Path(bad_name_configs[path_type]) / bad_name
        )

        with pytest.raises(ConfigError) as e:
            no_cfg_project.make_config_file(**bad_name_configs)

        assert (
            f"The {path_type} does not end in the project name: {no_cfg_project.project_name}."
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
        )

        # project 2 will not be found, because it does not
        # have a config file.
        os.mkdir(tmp_path / "projects" / "project_2")

        project_2 = DataShuttle("project_3")
        project_2.make_config_file(
            tmp_path / "project_3",
            tmp_path / "project_3",
            "local_filesystem",
        )

        project_paths = getters.get_existing_project_paths()

        assert sorted(project_paths) == [
            (tmp_path / "projects" / "project_1"),
            (tmp_path / "projects" / "project_3"),
        ]

    # --------------------------------------------------------------------------------------------------------------------
    # Utils
    # --------------------------------------------------------------------------------------------------------------------

    def check_config_reopen_and_check_config_again(self, project, *kwargs):
        """
        Check the config file and project.cfg against provided kwargs,
        delete the project and set up the project again,
        checking everything is loaded correctly.
        """
        test_utils.check_configs(project, kwargs[0])
        project_name = project.project_name

        del project  # del project is almost certainly unnecessary

        project = DataShuttle(project_name)

        test_utils.check_configs(project, kwargs[0])
