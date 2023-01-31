"""
Module to test command line interface. There are two approaches
to testing. The first utilised a second stream in
command_line_interface.py that relies on a protected
project name 'ds_protected_test_name'. CLI commands
with this project will output all arguments as simplejson
to stdout where they are read and tested here.

As a secondary check, functionality is tested for
all commands once. This is much less thorough
that API testing but as CLI is essentially a
wrapper for API this, along with checking
variables, is sufficient. However, it does
lead to some very similar logic tests between
this module and other tests.

NOTE: when testing these functions with breakpoint(),
the debugger is acting very strangely and breaks in
1 level lower than usual, requires 'u' to go
up a level. This is probably because testing in subprocess.
Might be better to use mock.
"""
import os

import pytest
import simplejson
import test_utils

from datashuttle.configs import canonical_configs
from datashuttle.configs.canonical_tags import tags

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"


class TestCommandLineInterface:
    @pytest.fixture(scope="function")
    def clean_project_name(self):
        """
        Create an empty project, but ensure no
        configs already exists, and delete created configs
        after test.
        """
        project_name = "test_configs"
        test_utils.delete_project_if_it_exists(project_name)
        yield project_name
        test_utils.delete_project_if_it_exists(project_name)

    @pytest.fixture(scope="function")
    def setup_project(self, tmp_path):
        """
        Setup a project with default configs to use
        for testing.

        # Note this fixture is a duplicate of project()
        in test_filesystem_transfer.py fixture
        """
        test_project_name = "test_command_line_interface"
        setup_project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )
        yield setup_project
        test_utils.teardown_project(cwd, setup_project)

    # ----------------------------------------------------------------------------------------------------------
    # Test CLI Variables are read and passed correctly
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_make_config_file_required_variables(self, sep, tmp_path):
        """
        Check the arguments passed to CLI make_config_file
        match those that are passed to wrapped API.

        First get default config arguments, run the
        CLI to make config file with defaults and check
        the internal arguments are ordered and in
        the expected form. Strip flags that are always false.
        Note use_behav is always on as a required argument,
        as at least one use_x argument must be true.

        Note any bool option is automatically included in the kwargs
        output from the CLI and passed to API. This is because initially
        any non-required argument defaulted to None. None is then
        stripped from the kwargs_ in the CLI code so these are not
        passed to the API and the default is used. However, for flags
        this is not possible, so the default value (False) is
        passed to the API. Here we need to delete the options
        that do not default to None on the CLI from the dictionary
        that is tested again (because, these are stripped in the CLI code)
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, required_arguments_only=True
        )

        stdout, stderr = test_utils.run_cli(
            f" make{sep}config{sep}file "
            + self.convert_kwargs_to_cli(required_options, sep)
        )

        try:
            __, kwargs_ = self.decode(stdout)
        except:
            breakpoint()

        # Remove items that are stripped from configs because they
        # default to None on the CLI
        default_options = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=True
        )
        del default_options["remote_host_id"]
        del default_options["remote_host_username"]
        del default_options["transfer_verbosity"]

        self.check_kwargs(default_options, kwargs_)

    def test_make_config_file_non_default_variables(self, tmp_path):
        """
        Check the variables for all configs (not just default)
        are correctly processed.
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=False
        )

        stdout, stderr = test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs)
        )

        args_, kwargs_ = self.decode(stdout)

        self.check_kwargs(changed_configs, kwargs_)

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_make_sub_dir_variable(self, sep):

        stdout, __ = test_utils.run_cli(
            f" make{sep}sub{sep}dir "
            f"--data_type all "
            f"--sub_names one "
            f"--ses_names two "
        )

        args_, kwargs_ = self.decode(stdout)

        assert args_ == []
        assert kwargs_["data_type"] == ["all"]
        assert kwargs_["sub_names"] == ["one"]
        assert kwargs_["ses_names"] == ["two"]

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_data_variables(self, upload_or_download, sep):
        """
        As upload_data and download_data take identical args,
        test both together.
        """
        stdout, __ = test_utils.run_cli(
            f" {upload_or_download}{sep}data "
            f"--data{sep}type all "
            f"--sub{sep}names one "
            f"--ses{sep}names two"
        )

        args_, kwargs_ = self.decode(stdout)
        self.check_upload_download_args(args_, kwargs_, dry_run_is=False)

        stdout, __ = test_utils.run_cli(
            f" {upload_or_download}_data "
            f"--data{sep}type all "
            f"--sub{sep}names one "
            f"--ses{sep}names two "
            f"--dry{sep}run"
        )

        args_, kwargs_ = self.decode(stdout)

        self.check_upload_download_args(args_, kwargs_, dry_run_is=True)

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_all_variables(
        self, setup_project, upload_or_download, sep
    ):
        """
        To quickly check whether this runs with both seps by only
        checking if no error is raised. This is also tested
        more thoroughly in test_upload_and_download_data()
        but without wasting time with seps.
        """
        stdout, stderr = test_utils.run_cli(
            f"{upload_or_download}{sep}all", setup_project.project_name
        )

        assert stderr == ""

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_dir_or_file(self, upload_or_download, sep):
        """
        As upload_data_dir_or_file and download_data_dir_or_file
        take identical args, test both together"""
        stdout, stderr = test_utils.run_cli(
            f" {upload_or_download}{sep}project{sep}dir{sep}or{sep}file /fake/filepath"
        )
        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == "/fake/filepath"
        assert kwargs_["dry_run"] is False

        stdout, stderr = test_utils.run_cli(
            f" {upload_or_download}{sep}project{sep}dir{sep}or{sep}file "
            f"/fake/filepath --dry{sep}run"
        )

        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == "/fake/filepath"
        assert kwargs_["dry_run"] is True

    @pytest.mark.parametrize(
        "command", ["make_sub_dir", "upload_data", "download_data"]
    )
    def test_multiple_inputs(self, command):
        """
        To process lists, a syntax "<>" is used
        to specify input is list. Check the passed
        varialbes are processed as expected.
        """
        stdout, stderr = test_utils.run_cli(
            f"{command} "
            f"--data_type all "
            f"--sub_names one  two 3 sub-004 sub-w23@ "
            f"--ses_names 5 06 007"
        )

        __, kwargs_ = self.decode(stdout)

        assert kwargs_["data_type"] == ["all"]
        assert kwargs_["sub_names"] == [
            "one",
            "two",
            "3",
            "sub-004",
            "sub-w23@",
        ]
        assert kwargs_["ses_names"] == ["5", "06", "007"]

    # ----------------------------------------------------------------------------------------------------------
    # Test CLI Functionality
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_update_config(self, clean_project_name, sep, tmp_path):
        """
        See test_update_config in test_configs.py.

        There is not a _variables (above) test for update_config
        because the arguments are converted to string
        in the body of project.update_config(), so that logging
        can capture everything. Thus, testing the variables
        that are json.dumps() for the test environment are not
        type-converted. As such, just test the whole
        workflow here, with both separators.
        """
        default_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=True
        )

        test_utils.run_cli(
            f" make{sep}config{sep}file "
            + self.convert_kwargs_to_cli(default_configs),
            clean_project_name,
        )

        not_set_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=False
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)
        test_utils.move_some_keys_to_end_of_dict(not_set_configs)

        for key, value in not_set_configs.items():

            format_value = (
                test_utils.add_quotes(value) if "path" in key else value
            )

            test_utils.run_cli(
                f" update{sep}config {key} {format_value}", clean_project_name
            )
            default_configs[key] = value

            test_utils.check_config_file(config_path, default_configs)

    def test_make_config_file_defaults(
        self,
        clean_project_name,
        tmp_path,
    ):
        """
        See test_config_defaults in test_configs.py
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, required_arguments_only=True
        )

        test_utils.run_cli(
            " make_config_file "
            + self.convert_kwargs_to_cli(required_options),
            clean_project_name,
        )

        default_options = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=True
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)

        test_utils.check_config_file(config_path, default_options)

    def test_make_config_file_not_defaults(
        self,
        clean_project_name,
        tmp_path,
    ):
        """
        see test_config_defaults in test_configs.py
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, set_as_defaults=False
        )

        test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs),
            clean_project_name,
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)

        test_utils.check_config_file(config_path, changed_configs)

    def test_make_sub_dir__(self, setup_project):
        """
        see test_filesystem_transfer.py
        """
        subs = ["sub-1_1", "sub-two-2", "sub-3_3-3=3"]
        ses = ["ses-123", "ses-hello_world"]

        test_utils.run_cli(
            f"make_sub_dir --data_type all --sub_names {self.to_cli_input(subs)} --ses_names {self.to_cli_input(ses)} ",  # noqa
            setup_project.project_name,
        )

        test_utils.check_directory_tree_is_correct(
            setup_project,
            base_dir=test_utils.get_rawdata_path(setup_project),
            subs=subs,
            sessions=ses,
            directory_used=test_utils.get_default_directory_used(),
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("use_all_alias", [True, False])
    def test_upload_and_download_data(
        self, setup_project, upload_or_download, use_all_alias
    ):
        """
        see test_filesystem_transfer.py
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project(
            setup_project,
            subs,
            sessions,
            "all",
        )

        __, base_path_to_check = test_utils.handle_upload_or_download(
            setup_project, upload_or_download
        )

        if use_all_alias:
            test_utils.run_cli(
                f"{upload_or_download}-all",
                setup_project.project_name,
            )
        else:
            test_utils.run_cli(
                f"{upload_or_download}_data "
                f"--data_type all "
                f"--sub_names all "
                f"--ses_names all",
                setup_project.project_name,
            )

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            base_path_to_check=os.path.join(
                base_path_to_check, setup_project.cfg.top_level_dir_name
            ),
            data_type_to_transfer=[
                flag.split("use_")[1]
                for flag in canonical_configs.get_data_types()
            ],
            subs_to_upload=subs,
            ses_to_upload=sessions,
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_upload_and_download_dir_or_file(
        self, setup_project, upload_or_download
    ):
        """
        see test_filesystem_transfer.py
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project(
            setup_project,
            subs,
            sessions,
            "all",
        )

        __, base_path_to_check = test_utils.handle_upload_or_download(
            setup_project, upload_or_download
        )

        test_utils.run_cli(
            f"{upload_or_download}_project_dir_or_file {subs[1]}/{sessions[0]}/ephys",
            setup_project.project_name,
        )

        path_to_check = (
            base_path_to_check / f"rawdata/{subs[1]}/{sessions[0]}/ephys"
        )

        assert path_to_check.is_dir()

    # ----------------------------------------------------------------------------------------------------------
    # Test Errors Propagate from API
    # ----------------------------------------------------------------------------------------------------------

    def test_warning_on_startup_cli(self, clean_project_name):
        """
        Check that warning from API are propagated to CLI
        """
        __, stderr = test_utils.run_cli("", clean_project_name)

        assert (
            "Configuration file has not been initialized. "
            "Use make_config_file() to setup before continuing." in stderr
        )

    def test_use_ssh_but_pass_no_ssh_options(self, clean_project_name):
        """
        Check that error from API are propagated to CLI
        """
        __, stderr = test_utils.run_cli(
            "make_config_file test_local_path test_remote_path ssh --use_behav",
            clean_project_name,
        )

        assert (
            "remote_host_id and remote_host_username are "
            "required if connection_method is ssh." in stderr
        )

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_check_format_names(self, clean_project_name, sep):
        """
        Check that testing the process names function outputs the
        properly processed names to stdout
        """
        stdout, stderr = test_utils.run_cli(
            f"check{sep}name{sep}formatting sub-001 1{tags('to')}02 --prefix sub-",
            clean_project_name,
        )

        assert "['sub-001', 'sub-01', 'sub-02']" in stdout

    # ----------------------------------------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------------------------------------

    def to_cli_input(self, list_):
        """
        Convert list to cli input
        """
        return " ".join(list_)

    def decode(self, stdout):
        """
        Read the simplejson.dumps() output from
        tested CLI.

        Pass a list of keys to strip in strip_keys,
        these are typically flag args that always
        return False by default e.g. --use-ephys
        """
        dumped_json = stdout.split("TEST_OUT_START:")[1]
        args_, kwargs_ = simplejson.loads(dumped_json)

        return args_, kwargs_

    def convert_kwargs_to_cli(self, kwargs, sep="-"):
        """
        Take a list of key-value pairs that make up
        the arguments we want to pass to CLI, and
        put them in correct format. This involves
        pre-pending "--argument_name" for non-positional
        arguments, and wrapping paths in quotes.
        """
        positionals = ["local_path", "remote_path", "connection_method"]

        prepend_positionals = ""
        for pos_arg in positionals:
            prepend_positionals += test_utils.add_quotes(kwargs[pos_arg]) + " "

        kwargs_list = []
        for key, value in kwargs.items():

            if key not in positionals:

                if "path" in key:
                    value = test_utils.add_quotes(value)
                else:
                    value = str(value)

                if key in canonical_configs.get_flags():
                    if value == "True":
                        argument = f"--{key.replace('_', sep)}"
                    else:
                        continue
                else:
                    argument = f"--{key.replace('_', sep)} {value}"
                kwargs_list.append(argument)

        kwargs_list = " ".join(kwargs_list)

        return prepend_positionals + kwargs_list

    def check_kwargs(self, required_options, kwargs_):

        for key in required_options.keys():
            assert kwargs_.pop(key) == required_options[key]
        assert kwargs_ == {}

    def check_upload_download_args(self, args_, kwargs_, dry_run_is):

        assert kwargs_["data_type"] == ["all"]
        assert kwargs_["sub_names"] == ["one"]
        assert kwargs_["ses_names"] == ["two"]
        assert kwargs_["dry_run"] is dry_run_is
        assert args_ == []
