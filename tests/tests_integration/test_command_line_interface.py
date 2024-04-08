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
"""

import argparse
import os

import pytest
import simplejson
import test_utils
from base import BaseTest

from datashuttle.command_line_interface import construct_parser
from datashuttle.configs import canonical_configs
from datashuttle.configs.canonical_tags import tags

# This is a special, protected project name.
# CLI commands with this project will output all arguments as simplejson
PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"


class TestCommandLineInterface(BaseTest):
    # -------------------------------------------------------------------------
    # Test CLI Variables are read and passed correctly
    # -------------------------------------------------------------------------

    def test_all_commands_appear_in_help(self):
        """
        Test that all subparsers defined in command_line_interface.py
        are displayed in the main --help list. This requires they have a help
        argument added on the subparser initialisation, e.g. help="".

        The below test requires some un-robust-seeming parsing
        of argparse output. First, the help string output
        by the CLI is split based on "}" character, as the
        argparse CLI output first has a list of all commands
        in {}, then a easier to read list of commands, that we want
        every command to be shown in, after this.

        Next, cycle through all subparsers and extract the name
        from the parser using the 'prog' attribute. This is
        well-defined so can be split from the number of spaces.

        Finally, check every parser is represented in the help string.
        """
        stdout, stderr = test_utils.run_cli("--help")
        cli_help_argument_list = stdout.split("}")[1]

        parser = construct_parser()

        all_subparsers = [
            subparser
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
            for _, subparser in action.choices.items()
        ]
        for subparser in all_subparsers:
            command_name = subparser.prog.split(" ")[3]

            assert command_name in cli_help_argument_list, (
                f"The command {command_name} is defined "
                f"in command_line_interface"
                f"but does not have a help string. Add an empty help="
                " to the parser"
                f"to resolve this (see command_line_interface.py for examples)."
            )

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_make_config_file_required_variables(self, sep, tmp_path):
        """
        Check the arguments passed to CLI make_config_file
        match those that are passed to wrapped API.

        First get default config arguments, run the
        CLI to make config file with defaults and check
        the internal arguments are ordered and in
        the expected form. Strip flags that are always false.

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
            tmp_path, PROTECTED_TEST_PROJECT_NAME, required_arguments_only=True
        )

        stdout, stderr = test_utils.run_cli(
            f" make{sep}config{sep}file "
            + self.convert_kwargs_to_cli(required_options, sep)
        )

        _, kwargs_ = self.decode(stdout)

        # Remove items that are stripped from configs because they
        # default to None on the CLI
        default_options = test_utils.get_test_config_arguments_dict(
            tmp_path, PROTECTED_TEST_PROJECT_NAME, set_as_defaults=True
        )
        del default_options["central_host_id"]
        del default_options["central_host_username"]
        del default_options["transfer_verbosity"]

        self.check_kwargs(default_options, kwargs_)

    def test_make_config_file_non_default_variables(self, tmp_path):
        """
        Check the variables for all configs (not just default)
        are correctly processed.
        """
        changed_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, PROTECTED_TEST_PROJECT_NAME, set_as_defaults=False
        )

        stdout, stderr = test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs)
        )

        args_, kwargs_ = self.decode(stdout)

        self.check_kwargs(changed_configs, kwargs_)

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_create_folders_variable(self, sep):
        stdout, _ = test_utils.run_cli(
            f" create{sep}folders "
            f"--datatype all "
            f"--sub_names 001 "
            f"--ses_names 002 "
        )

        args_, kwargs_ = self.decode(stdout)

        assert args_ == []
        assert kwargs_["datatype"] == ["all"]
        assert kwargs_["sub_names"] == ["001"]
        assert kwargs_["ses_names"] == ["002"]

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_variables(self, upload_or_download, sep):
        """
        As upload and download take identical args,
        test both together.
        """
        stdout, _ = test_utils.run_cli(
            f" {upload_or_download} "
            f"--datatype all "
            f"--sub{sep}names one "
            f"--ses{sep}names two"
        )

        args_, kwargs_ = self.decode(stdout)
        self.check_upload_download_args(args_, kwargs_, dry_run_is=False)

        stdout, _ = test_utils.run_cli(
            f" {upload_or_download} "
            f"--datatype all "
            f"--sub{sep}names one "
            f"--ses{sep}names two "
            f"--dry{sep}run"
        )

        args_, kwargs_ = self.decode(stdout)

        self.check_upload_download_args(args_, kwargs_, dry_run_is=True)

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_all_variables(
        self, project, upload_or_download, sep
    ):
        """
        To quickly check whether this runs with both seps by only
        checking if no error is raised. This is also tested
        more thoroughly in test_upload_and_download()
        but without wasting time with seps.
        """
        stdout, stderr = test_utils.run_cli(
            f"{upload_or_download}{sep}all", project.project_name
        )

        assert stderr == ""

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_entire_project_variables(
        self, project, upload_or_download, sep
    ):
        """
        see test_upload_download_all_variables()
        """
        stdout, stderr = test_utils.run_cli(
            f"{upload_or_download}{sep}entire{sep}project",
            project.project_name,
        )

        assert stderr == ""

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_upload_download_folder_or_file(self, upload_or_download, sep):
        """
        As upload_folder_or_file and download_folder_or_file
        take identical args, test both together"""
        stdout, stderr = test_utils.run_cli(
            f" {upload_or_download}{sep}specific{sep}folder{sep}or{sep}file "
            f"/fake/filepath"
        )
        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == "/fake/filepath"
        assert kwargs_["dry_run"] is False

        stdout, stderr = test_utils.run_cli(
            f" {upload_or_download}{sep}specific{sep}folder{sep}or{sep}file "
            f"/fake/filepath --dry{sep}run"
        )

        args_, kwargs_ = self.decode(stdout)

        assert args_[0] == "/fake/filepath"
        assert kwargs_["dry_run"] is True

    @pytest.mark.parametrize(
        "command", ["create_folders", "upload", "download"]
    )
    def test_multiple_inputs(self, command):
        """
        To process lists, a syntax "<>" is used
        to specify input is list. Check the passed
        variables are processed as expected.
        """
        stdout, stderr = test_utils.run_cli(
            f"{command} "
            f"--datatype all "
            f"--sub_names one  two 3 sub-004 sub-w23@ "
            f"--ses_names 5 06 007"
        )

        _, kwargs_ = self.decode(stdout)

        assert kwargs_["datatype"] == ["all"]
        assert kwargs_["sub_names"] == [
            "one",
            "two",
            "3",
            "sub-004",
            "sub-w23@",
        ]
        assert kwargs_["ses_names"] == ["5", "06", "007"]

    # -------------------------------------------------------------------------
    # Test CLI Functionality
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_update_config_file(self, clean_project_name, sep, tmp_path):
        """
        Set up a project then up all configs with new configs
        and check these are all loaded correctly.
        """
        default_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, clean_project_name, set_as_defaults=True
        )

        test_utils.run_cli(
            f" make{sep}config{sep}file "
            + self.convert_kwargs_to_cli(default_configs),
            clean_project_name,
        )

        not_set_configs = test_utils.get_test_config_arguments_dict(
            tmp_path, clean_project_name, set_as_defaults=False
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)
        test_utils.move_some_keys_to_end_of_dict(not_set_configs)

        argument_list = ""
        for key, value in not_set_configs.items():
            format_value = (
                test_utils.add_quotes(value) if "path" in key else value
            )
            argument_list += f"--{key} {format_value} "

        test_utils.run_cli(
            f" update{sep}config{sep}file {argument_list}", clean_project_name
        )

        test_utils.check_config_file(config_path, not_set_configs)

    def test_make_config_file_defaults(
        self,
        clean_project_name,
        tmp_path,
    ):
        """
        See test_config_defaults in test_configs.py
        """
        required_options = test_utils.get_test_config_arguments_dict(
            tmp_path, clean_project_name, required_arguments_only=True
        )

        test_utils.run_cli(
            " make_config_file "
            + self.convert_kwargs_to_cli(required_options),
            clean_project_name,
        )

        default_options = test_utils.get_test_config_arguments_dict(
            tmp_path, clean_project_name, set_as_defaults=True
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
            tmp_path, clean_project_name, set_as_defaults=False
        )

        test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs),
            clean_project_name,
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)
        test_utils.check_config_file(config_path, changed_configs)

    def test_create_folders___(self, project):
        """
        see test_filesystem_transfer.py
        """
        subs = ["sub-011", "sub-002", "sub-333"]
        ses = ["ses-123", "ses-999"]

        test_utils.run_cli(
            f"create_folders --datatype all --sub_names {self.to_cli_input(subs)} --ses_names {self.to_cli_input(ses)} ",
            project.project_name,
        )
        test_utils.check_folder_tree_is_correct(
            base_folder=test_utils.get_top_level_folder_path(project),
            subs=subs,
            sessions=ses,
            folder_used=test_utils.get_all_folders_used(),
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize(
        "transfer_method", ["standard", "all_alias", "entire_project"]
    )
    def test_upload_and_download(
        self, project, upload_or_download, transfer_method
    ):
        """
        This tests whether basic transfer works through CLI.
        see test_filesystem_transfer.py for more extensive tests.
        "_" vs. "-" command separators are not tested here to avoid
        adding another enumeration, as these tests are slow.
        Testing that the command runs with both separators is done above,
        in test_upload_download_all_variables() and
        test_upload_download_variables()
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project_folders(
            project,
            subs,
            sessions,
            "all",
        )

        _, base_path_to_check = test_utils.handle_upload_or_download(
            project, upload_or_download
        )

        if transfer_method == "all_alias":
            test_utils.run_cli(
                f"{upload_or_download}-all",
                project.project_name,
            )
        elif transfer_method == "standard":
            test_utils.run_cli(
                f"{upload_or_download} "
                f"--datatype all "
                f"--sub_names all "
                f"--ses_names all",
                project.project_name,
            )
        elif transfer_method == "entire_project":
            test_utils.run_cli(
                f"{upload_or_download}_entire_project",
                project.project_name,
            )

        test_utils.check_datatype_sub_ses_uploaded_correctly(
            base_path_to_check=os.path.join(
                base_path_to_check, project.cfg.top_level_folder
            ),
            datatype_to_transfer=canonical_configs.get_datatypes(),
            subs_to_upload=subs,
            ses_to_upload=sessions,
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_upload_and_download_folder_or_file(
        self, project, upload_or_download
    ):
        """
        see test_filesystem_transfer.py
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project_folders(
            project,
            subs,
            sessions,
            "all",
        )

        _, base_path_to_check = test_utils.handle_upload_or_download(
            project, upload_or_download
        )

        test_utils.run_cli(
            f"{upload_or_download}_specific_folder_or_file "
            f"{subs[1]}/{sessions[0]}/ephys/**",
            project.project_name,
        )

        path_to_check = (
            base_path_to_check / f"rawdata/{subs[1]}/{sessions[0]}/ephys"
        )

        assert path_to_check.is_dir()

    # -------------------------------------------------------------------------
    # Test Errors Propagate from API
    # -------------------------------------------------------------------------

    def test_use_ssh_but_pass_no_ssh_options(self, clean_project_name):
        """
        Check that error from API are propagated to CLI
        """
        _, stderr = test_utils.run_cli(
            f"make_config_file {clean_project_name} {clean_project_name} ssh",
            clean_project_name,
        )

        assert (
            "'central_host_id' and 'central_host_username' are "
            "required if 'connection_method' is 'ssh'." in stderr
        )

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_check_format_names(self, clean_project_name, sep):
        """
        Check that testing the process names function outputs the
        properly processed names to stdout
        """
        stdout, stderr = test_utils.run_cli(
            f"check{sep}name{sep}formatting sub --names 1{tags('to')}03",
            clean_project_name,
        )
        assert "['sub-01', 'sub-02', 'sub-03']" in stdout

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_set_top_level_folder(self, project, sep):
        """
        Test that the top level folder is "rawdata" by default,
        setting the top level folder to a new folder ("derivatives")
        updates the top level folder correctly. Finally, test
        passing a not-allowed top-level-folder to
        set-top-level-folder raises an error.
        """
        stdout, _ = test_utils.run_cli(
            f"get{sep}top{sep}level{sep}folder", project.project_name
        )

        assert "rawdata" in stdout

        stdout, stderr = test_utils.run_cli(
            f"set{sep}top{sep}level{sep}folder derivatives",
            project.project_name,
        )
        assert "derivatives" in stdout

        stdout, _ = test_utils.run_cli(
            f"get{sep}top{sep}level{sep}folder", project.project_name
        )

        assert "derivatives" in stdout

        _, stderr = test_utils.run_cli(
            f"set{sep}top{sep}level{sep}folder NOT_RECOGNISED",
            project.project_name,
        )

        assert (
            "Folder name: NOT_RECOGNISED is not in permitted top-level folder names"
            in stderr
        )

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_cli_get_paths(self, project, sep):
        """
        Check that all CLI commands to return a path
        show the correct path
        """
        stdout, _ = test_utils.run_cli(
            f"get{sep}local{sep}path", project.project_name
        )
        assert str(project.get_local_path()) in stdout

        stdout, _ = test_utils.run_cli(
            f"get{sep}central{sep}path", project.project_name
        )
        assert str(project.get_central_path()) in stdout

        stdout, _ = test_utils.run_cli(
            f"get{sep}datashuttle{sep}path", project.project_name
        )
        assert str(project.get_datashuttle_path()) in stdout

        stdout, _ = test_utils.run_cli(
            f"get{sep}config{sep}path", project.project_name
        )
        assert str(project.get_config_path()) in stdout

        stdout, _ = test_utils.run_cli(
            f"get{sep}logging{sep}path", project.project_name
        )
        assert str(project.get_logging_path()) in stdout

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_cli_get_top_level_folder(self, project, sep):
        """
        Check the CLI command to get the top-level-folder
        shows the correct name.
        """
        project.set_top_level_folder("derivatives")

        stdout, stderr = test_utils.run_cli(
            f"get{sep}top{sep}level{sep}folder", project.project_name
        )
        assert str(project.get_top_level_folder()) in stdout

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_cli_existing_projects(self, project, sep):
        """
        Check that the CLI argument to get existing projects
        works and returns existing projects (1 is tested).
        """
        stdout, stderr = test_utils.run_cli(
            f"get{sep}existing{sep}projects", project.project_name
        )
        assert str(project.get_existing_projects()[0].as_posix()) in stdout

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_get_cli_get_next_ses_sub_number(self, project, sep):
        """
        Check the CLI arguments to get the next subject
        or session number, shows the correct sub / ses number.
        """
        project.create_folders("sub-001", "ses-001")

        stdout, _ = test_utils.run_cli(
            f"get{sep}next{sep}sub{sep}number", project.project_name
        )
        assert "sub-002" in stdout

        stdout, _ = test_utils.run_cli(
            f"get{sep}next{sep}ses{sep}number sub-001", project.project_name
        )
        assert "ses-002" in stdout

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_cli_show_functions(self, sep, project):
        """
        Check that the CLI arguments testing the
        shower-functions return something sensible.
        """
        stdout, _ = test_utils.run_cli(
            f"show{sep}configs", project.project_name
        )

        assert str(project.cfg["local_path"].as_posix()) in stdout

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_cli_validate_project(self, project, sep):
        """
        Check the at CLI command to validate project returns
        some validation, indicating the underlying function
        is called correctly.
        """
        project.create_folders("sub-001")
        os.makedirs(project.cfg["central_path"] / "rawdata" / "sub-1")

        _, stderr = test_utils.run_cli(
            f"validate{sep}project", project.project_name
        )

        assert "A sub already exists" in stderr

    @pytest.mark.parametrize("sep", ["-", "_"])
    def test_cli_setup_ssh_connection(self, project, sep):
        """
        Test the CLI argument to set up an ssh connection runs,
        does not check functionality just that it is calling the
        underlying API properly.
        """
        _, stderr = test_utils.run_cli(
            f"setup{sep}ssh{sep}connection{sep}to{sep}central{sep}server",
            project.project_name,
        )
        assert "Cannot setup SSH connection" in stderr

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

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
        prepending "--argument_name" for non-positional
        arguments, and wrapping paths in quotes.
        """
        positionals = ["local_path", "central_path", "connection_method"]

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
        assert kwargs_["datatype"] == ["all"]
        assert kwargs_["sub_names"] == ["one"]
        assert kwargs_["ses_names"] == ["two"]
        assert kwargs_["dry_run"] is dry_run_is
        assert args_ == []
