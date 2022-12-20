"""
"""
import logging

import pytest
import test_utils

# from datashuttle.configs import canonical_configs
from datashuttle.datashuttle import DataShuttle


class TestCommandLineInterface:
    @pytest.fixture(scope="function")
    def clean_project_name(self):
        """
        Create an empty project, but ensure no
        configs already exists, and delete created configs
        after test.
        """
        project_name = "test_logging"
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
        test_project_name = "test_logging"
        setup_project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )
        yield setup_project
        test_utils.teardown_project(cwd, setup_project)

    # ----------------------------------------------------------------------------------------------------------
    # Test Public API Logging
    # ----------------------------------------------------------------------------------------------------------

    def test_logging_update_config(self, clean_project_name, caplog):
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
        project = DataShuttle(clean_project_name)

        with caplog.at_level(logging.INFO, logger="fancylog_"):
            project.make_config_file(
                "one", "two", "local_filesystem", use_behav=True
            )
        breakpoint()

        breakpoint()
        # import glob

        # log_filepath = glob.glob(str(project._logging_path / "*.log"))

        #  assert len(log_filepath) == 1
        #   log_filepath = log_filepath[0]

        #    with open(log_filepath, "r") as file:
        #         log = file.read()

        breakpoint()

        # will need to test failure

    """
    def test_make_config_file_defaults(
        self,
        clean_project_name,
    ):
        required_options = test_utils.get_test_config_arguments_dict(
            required_arguments_only=True
        )

        test_utils.run_cli(
            " make_config_file "
            + self.convert_kwargs_to_cli(required_options),
            clean_project_name,
        )

        default_options = test_utils.get_test_config_arguments_dict(
            set_as_defaults=True
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)

        test_utils.check_config_file(config_path, default_options)

    def test_make_config_file_not_defaults(
        self,
        clean_project_name,
    ):
        changed_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=False
        )

        test_utils.run_cli(
            " make_config_file " + self.convert_kwargs_to_cli(changed_configs),
            clean_project_name,
        )

        config_path = test_utils.get_config_path_with_cli(clean_project_name)

        test_utils.check_config_file(config_path, changed_configs)

    def test_make_sub_dir__(self, setup_project):
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
                base_path_to_check, setup_project._top_level_dir_name
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
        __, stderr = test_utils.run_cli("", clean_project_name)

        assert (
            "Configuration file has not been initialized. "
            "Use make_config_file() to setup before continuing." in stderr
        )

    def test_use_ssh_but_pass_no_ssh_options(self, clean_project_name):
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
        stdout, __ = test_utils.run_cli(
            f"check{sep}name{sep}processing sub-001 1@TO@02 --prefix sub-",
            clean_project_name,
        )

        assert "['sub-001', 'sub-01', 'sub-02']" in stdout

    # ----------------------------------------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------------------------------------

    def to_cli_input(self, list_):
        return " ".join(list_)

    def decode(self, stdout):
        dumped_json = stdout.split("TEST_OUT_START:")[1]
        args_, kwargs_ = simplejson.loads(dumped_json)

        return args_, kwargs_

    def convert_kwargs_to_cli(self, kwargs, sep="-"):

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
    """
