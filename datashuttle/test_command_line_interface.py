import os
import pathlib
import warnings

import pytest
import simplejson
import yaml
from click.testing import CliRunner

from datashuttle.command_line_interface import entry
from datashuttle.datashuttle import DataShuttle
from tests import test_configs, test_utils

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"

# setup_ssh_connection_to_remote_server TODO


class TestCommandLineInterface:
    def decode(self, stdout):
        dumped_json = stdout.split("TEST_OUT_START:")[1]
        args_, kwargs_ = simplejson.loads(dumped_json)
        return args_, kwargs_

    def convert_kwargs_to_cli(self, kwargs):
        args_list = " ".join(
            "--" + k + " " + str(v) for k, v in kwargs.items()
        )
        return args_list

    def check_kwargs(self, required_options, kwargs_):
        for key in required_options.keys():
            assert kwargs_.pop(key) == required_options[key]
        assert kwargs_ == {}

    def check_config_args(self, args_, options):
        assert len(args_) == 2
        assert args_[0] == options.pop("local_path")
        assert args_[1] is options.pop("ssh_to_remote")

    # Configs ----------------------------------------------------------------------------------------------

    def test_make_config_file_required_variables(self):
        """ """
        required_options = test_utils.get_test_config_arguments_dict(
            required_arguments_only=True
        )

        stdout, __ = test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(required_options)
        )
        args_, kwargs_ = self.decode(stdout)

        self.check_config_args(args_, required_options)
        self.check_kwargs(required_options, kwargs_)

    def test_make_config_file_non_default_variables(self):
        """ """
        changed_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=False
        )

        stdout, __ = test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs)
        )
        args_, kwargs_ = self.decode(stdout)

        self.check_config_args(args_, changed_configs)
        self.check_kwargs(changed_configs, kwargs_)

    # Update Configs  ----------------------------------------------------------------------------------------------

    def test_update_config_variables(self):
        """"""
        changed_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=False
        )

        for key, value in changed_configs.items():
            stdout, __ = test_utils.run_cli(f" update_config {key} {value}")
            args_, __ = self.decode(stdout)

            assert key == args_[0]
            assert value == args_[1]

    # Make Sub Dir  ----------------------------------------------------------------------------------------------

    def check_upload_download_args(self, args_, kwargs_, preview_is):
        assert args_[0] == ["all"]
        assert args_[1] == ["one"]
        assert args_[2] == ["two"]
        assert args_[3] is preview_is
        assert kwargs_ == {}

    def test_make_sub_dir_variable(self):
        """"""
        stdout, __ = test_utils.run_cli(
            " make_sub_dir --experiment_type all --sub_names one --ses_names two --make_ses_tree False"
        )
        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == ["all"]
        assert args_[1] == ["one"]
        assert kwargs_["ses_names"] == ["two"]
        assert kwargs_["make_ses_tree"] is False

    # Upload / Download Data  ----------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_upload_download_data_variables(self, upload_or_download):
        """"""
        stdout, __ = test_utils.run_cli(
            f" {upload_or_download}_data --experiment_type all --sub_names one --ses_names two"
        )
        args_, kwargs_ = self.decode(stdout)
        self.check_upload_download_args(args_, kwargs_, preview_is=False)

        stdout, __ = test_utils.run_cli(
            f" {upload_or_download}_data --experiment_type all --sub_names one --ses_names two --preview"
        )
        args_, kwargs_ = self.decode(stdout)
        self.check_upload_download_args(args_, kwargs_, preview_is=True)

    #  Upload / Download Project Dir or File ----------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_upload_download_dir_or_file(self, upload_or_download):
        """ """
        stdout, __ = test_utils.run_cli(
            f" {upload_or_download}_project_dir_or_file /fake/filepath"
        )
        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == "/fake/filepath"
        assert args_[1] is False
        assert kwargs_ == {}

        stdout, __ = test_utils.run_cli(
            f" {upload_or_download}_project_dir_or_file /fake/filepath --preview"
        )
        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == "/fake/filepath"
        assert args_[1] is True
        assert kwargs_ == {}

    # -----------------------------------------------------------------------------------------
    # Test Functionality
    # -----------------------------------------------------------------------------------------

    def test_update_config(self):
        """ """
        project_name = "test_configs"
        test_utils.setup_project_default_configs(project_name)

        not_set_configs = test_utils.get_test_config_arguments_dict(
            DataShuttle(project_name)
        )

        for key, value in not_set_configs.items():
            test_utils.run_cli(f" update_config {key} {value}")

            test_utils.check_configs(project, default_configs)

    def test_make_config_file_defaults(
        self,
    ):  # similar to test_config_defaults
        """ """
        project_name = "test_configs"
        test_utils.delete_project_if_it_exists(project_name)

        required_options = test_utils.get_test_config_arguments_dict(
            required_arguments_only=True
        )

        test_utils.run_cli(
            " make_config_file "
            + self.convert_kwargs_to_cli(required_options),
            project_name,
        )

        default_options = test_utils.get_test_config_arguments_dict(
            set_as_defaults=True
        )

        config_path = test_utils.get_config_path_with_cli(project_name)

        test_utils.check_config_file(config_path, default_options)

        test_utils.delete_project_if_it_exists(project_name)  # TODO: teardown

    def test_make_config_file_not_defaults(
        self,
    ):  # similar to test_config_defaults
        """ """
        project_name = "test_configs"
        test_utils.delete_project_if_it_exists(project_name)

        changed_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=False
        )

        test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs),
            project_name,
        )

        test_utils.check_configs(DataShuttle(project_name), changed_configs)

        test_utils.delete_project_if_it_exists(project_name)  # TODO: teardown

    # -----------------------------------------------------------------------------------------
    # Test Getters, Setters, <> Syntax
    # -----------------------------------------------------------------------------------------


# TODO!: test <> syntax

# make a clean project and test configs are all set as defults! test_configs() test_config_defaults

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
