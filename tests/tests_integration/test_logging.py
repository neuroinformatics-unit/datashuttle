import glob
import os

import pytest
import test_utils

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

        self.delete_log_files(setup_project._logging_path)

        yield setup_project
        test_utils.teardown_project(cwd, setup_project)

    # ----------------------------------------------------------------------------------------------------------
    # Test Public API Logging
    # ----------------------------------------------------------------------------------------------------------

    def read_log_file(self, logging_path):

        log_filepath = glob.glob(str(logging_path / "*.log"))

        assert len(log_filepath) == 1, (
            f"there should only be one log "
            f"in log output path {logging_path}"
        )
        log_filepath = log_filepath[0]

        with open(log_filepath, "r") as file:
            log = file.read()

        return log

    def delete_log_files(self, logging_path):
        test_utils.unlink_log_filehandler()
        logs = glob.glob((str(logging_path / "*.log")))
        for log in logs:
            os.remove(log)

    def test_logs_make_config_file(self, clean_project_name):
        """"""
        project = DataShuttle(clean_project_name)

        project.make_config_file(
            "one", "two", "local_filesystem", use_behav=True
        )

        log = self.read_log_file(project._logging_path)

        assert "Starting make_config_file" in log
        assert "Successfully created rclone config." in log
        assert (
            "Configuration file has been saved and options loaded into datashuttle."
            in log
        )
        assert "Update successful. New config file:" in log

    def test_logs_update_config(self, setup_project):

        setup_project.update_config("local_path", "test_path")

        log = self.read_log_file(setup_project._logging_path)

        assert "Starting update_config" in log
        assert "local_path has been updated to test_path" in log
        assert "Update successful. New config file:" in log
        assert """ "local_path": "test_path",\n """ in log

    def test_logs_supply_config(self, setup_project):
        """"""
        new_configs_path = test_utils.make_correct_supply_config_file(
            setup_project
        )

        setup_project.supply_config_file(new_configs_path, warn=False)

        log = self.read_log_file(setup_project._logging_path)

        assert "supply_config_file" in log
        assert "Update successful. New config file: " in log
        assert """ "local_path": "C:/test/test_ local/test_edit",\n """ in log

    def test_make_sub_dir__(self, setup_project):

        subs = ["sub-1_1", "sub-002@TO@004"]
        ses = ["ses-123", "ses-hello_world"]

        setup_project.make_sub_dir(subs, ses, data_type="all")

        log = self.read_log_file(setup_project._logging_path)

        assert "Formatting Names..." in log
        assert "sub_names: ['sub-1_1', 'sub-002@TO@004']" in log
        assert "ses_names: ['ses-123', 'ses-hello_world']" in log
        assert (
            "formatted_sub_names: ['sub-1_1', 'sub-002', 'sub-003', 'sub-004']"
            in log
        )
        assert "formatted_ses_names: ['ses-123', 'ses-hello_world']" in log
        assert "Made directory at path:" in log
        assert (
            os.path.join("test_logging", "local", "rawdata", "sub-1_1") in log
        )
        assert (
            os.path.join(
                "test_logging",
                "local",
                "rawdata",
                "sub-1_1",
                "ses-123",
                "funcimg",
                ".datashuttle_meta",
            )
            in log
        )
        assert (
            os.path.join(
                "test_logging",
                "local",
                "rawdata",
                "sub-002",
                "ses-123",
                "funcimg",
            )
            in log
        )
        assert (
            os.path.join(
                "test_logging",
                "local",
                "rawdata",
                "sub-004",
                "ses-hello_world",
            )
            in log
        )
        assert "Finished file creation. Local folder tree is now:" in log

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("use_all_alias", [True, False])
    def test_logs_upload_and_download_data(
        self, setup_project, upload_or_download, use_all_alias
    ):
        subs = ["sub-1_1"]
        sessions = ["ses-123"]

        test_utils.make_and_check_local_project(
            setup_project,
            subs,
            sessions,
            "all",
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(
            setup_project,
            upload_or_download,
            use_all_alias,
        )
        self.delete_log_files(setup_project._logging_path)

        transfer_function() if use_all_alias else transfer_function(
            "all", "all", "all"
        )

        log = self.read_log_file(setup_project._logging_path)

        suffix = "_all" if use_all_alias else "_data"

        assert f"Starting {upload_or_download}{suffix}" in log
        assert "Creating backend with remote" in log
        assert "Using config file from" in log
        assert "Local file system at" in log
        assert "/test_logging/local/rawdata/sub-1_1/histology"
        assert (
            "/test_logging/remote/rawdata/sub-1_1/histology: copied 1 directories"
            in log
        )
        assert "/test_logging/local/rawdata/sub-1_1/ses-123/behav" in log
        assert "/test_logging/remote/rawdata/sub-1_1/ses-123/behav" in log
        assert "Waiting for checks to finish" in log
        assert "Transferred:   	          0 B / 0 B, -, 0 B/s, ETA -" in log
        assert "Elapsed time:         0.0s" in log

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_logs_upload_and_download_dir_or_file(
        self, setup_project, upload_or_download
    ):
        """ """
        test_utils.make_and_check_local_project(
            setup_project,
            subs=["sub-001"],
            sessions=["ses-001"],
            data_type="all",
        )
        test_utils.handle_upload_or_download(
            setup_project,
            upload_or_download,
        )
        self.delete_log_files(setup_project._logging_path)

        if upload_or_download == "upload":
            setup_project.upload_project_dir_or_file("sub-001/ses-001")
        else:
            setup_project.download_project_dir_or_file("sub-001/ses-001")

        log = self.read_log_file(setup_project._logging_path)

        assert f"Starting {upload_or_download}_project_dir_or_file" in log
        assert "/rawdata/sub-001/ses-001" in log
        assert "Using config file from" in log
        assert "/rawdata/sub-001/ses-001" in log
        assert "/rawdata/sub-001/ses-001" in log
        assert "Waiting for checks to finish" in log
        assert "behav/.datashuttle_meta: Making directory" in log
        assert "ephys/.datashuttle_meta: Making directory" in log
        assert "funcimg/.datashuttle_meta: Making directory" in log

    # ----------------------------------------------------------------------------------------------------------
    # Check errors propagate
    # ----------------------------------------------------------------------------------------------------------

    def test_logs_check_update_config_error(self, setup_project):
        """"""
        with pytest.raises(BaseException):
            setup_project.update_config("connection_method", "ssh")

        log = self.read_log_file(setup_project._logging_path)

        assert (
            "remote_host_id and remote_host_username are required if connection_method is ssh."
            in log
        )
        assert "connection_method was not updated" in log

    def test_logs_bad_make_sub_dir_error(self, setup_project):
        """"""
        setup_project.make_sub_dir("sub-001", data_type="all")
        self.delete_log_files(setup_project._logging_path)

        with pytest.raises(BaseException):
            setup_project.make_sub_dir("sub-001", data_type="all")

        log = self.read_log_file(setup_project._logging_path)

        assert (
            "Cannot make directories. The key sub-001 already exists in the project"
            in log
        )
