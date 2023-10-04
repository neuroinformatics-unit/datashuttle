import glob
import os
import platform
from pathlib import Path

import pytest
import test_utils

from datashuttle.configs.canonical_tags import tags
from datashuttle.datashuttle import DataShuttle
from datashuttle.utils import ds_logger

BAD_WINDOWS_FILECHAR = "?"  # a symbol that will create an error when trying to make a file with this name.
# this is only tested in windows as nearly any char is allowed for macos and linux
IS_WINDOWS = platform.system() == "Windows"


class TestCommandLineInterface:
    @pytest.fixture(scope="function")
    def clean_project_name(self):
        """
        Create an empty project, but ensure no
        configs already exists, and delete created configs
        after test.

        Switch on datashuttle logging as required for
        these tests, then turn back off during tear-down.
        """
        project_name = "test_logging"
        test_utils.delete_project_if_it_exists(project_name)
        test_utils.set_datashuttle_loggers(disable=False)

        yield project_name
        test_utils.delete_project_if_it_exists(project_name)
        test_utils.set_datashuttle_loggers(disable=True)

    @pytest.fixture(scope="function")
    def setup_project(self, tmp_path):
        """
        Setup a project with default configs to use
        for testing.

        Switch on datashuttle logging as required for
        these tests, then turn back off during tear-down.
        """
        test_project_name = "test_logging"
        setup_project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )

        self.delete_log_files(setup_project.cfg.logging_path)

        test_utils.set_datashuttle_loggers(disable=False)

        yield setup_project

        test_utils.teardown_project(cwd, setup_project)
        test_utils.set_datashuttle_loggers(disable=True)

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
        ds_logger.close_log_filehandler()
        logs = glob.glob((str(logging_path / "*.log")))
        for log in logs:
            os.remove(log)

    def test_logs_make_config_file(self, clean_project_name, tmp_path):
        """"""
        project = DataShuttle(clean_project_name)

        project.make_config_file(
            tmp_path, "two", "local_filesystem", use_behav=True
        )

        log = self.read_log_file(project.cfg.logging_path)

        assert "Starting logging for command make_config_file" in log
        assert "\nVariablesState:\nlocals: {'local_path':" in log
        assert "Successfully created rclone config." in log
        assert (
            "Configuration file has been saved and options loaded into datashuttle."
            in log
        )
        assert "Update successful. New config file:" in log

    def test_logs_update_config(self, setup_project):
        setup_project.update_config("central_host_id", "test_id")

        log = self.read_log_file(setup_project.cfg.logging_path)

        assert "Starting logging for command update_config" in log
        assert (
            "\n\nVariablesState:\nlocals: {'option_key': 'central_host_id'"
            in log
        )
        assert "central_host_id has been updated to test_id" in log
        assert "Update successful. New config file:" in log
        assert """ "central_host_id": "test_id",\n """ in log

    def test_logs_supply_config(self, setup_project, tmp_path):
        """"""
        new_configs_path, _ = test_utils.make_correct_supply_config_file(
            setup_project, tmp_path
        )
        self.delete_log_files(setup_project.cfg.logging_path)
        orig_project_path = setup_project.cfg.logging_path

        setup_project.supply_config_file(new_configs_path, warn=False)

        log = self.read_log_file(orig_project_path)

        assert "supply_config_file" in log
        assert "\n\nVariablesState:\nlocals: {'input_path_to_config':" in log
        assert "Update successful. New config file: " in log
        assert (
            f""" "local_path": "{setup_project.cfg['local_path'].as_posix()}",\n """
            in log
        )

    def test_make_sub_folders(self, setup_project):
        subs = ["sub-11", f"sub-002{tags('to')}004"]
        ses = ["ses-123", "ses-101"]

        setup_project.make_sub_folders(subs, ses, datatype="all")

        log = self.read_log_file(setup_project.cfg.logging_path)

        assert "Formatting Names..." in log

        assert (
            "\n\nVariablesState:\nlocals: {'sub_names': ['sub-11', "
            "'sub-002@TO@004'], 'ses_names': ['ses-123', 'ses-101'], "
            "'datatype': 'all'}\ncfg: {'local_path':" in log
        )

        assert f"sub_names: ['sub-11', 'sub-002{tags('to')}004']" in log
        assert "ses_names: ['ses-123', 'ses-101']" in log
        assert (
            "formatted_sub_names: ['sub-11', 'sub-002', 'sub-003', 'sub-004']"
            in log
        )
        assert "formatted_ses_names: ['ses-123', 'ses-101']" in log
        assert "Made folder at path:" in log

        assert (
            str(Path("test_logging") / "local" / "rawdata" / "sub-11") in log
        )
        assert (
            str(
                Path(
                    "test_logging",
                    "local",
                    "rawdata",
                    "sub-11",
                    "ses-123",
                    "funcimg",
                    ".datashuttle_meta",
                )
            )
            in log
        )
        assert (
            str(
                Path(
                    "test_logging",
                    "local",
                    "rawdata",
                    "sub-002",
                    "ses-123",
                    "funcimg",
                )
            )
            in log
        )
        assert (
            str(
                Path(
                    "test_logging",
                    "local",
                    "rawdata",
                    "sub-004",
                    "ses-101",
                )
            )
            in log
        )
        assert "Finished file creation. Local folder tree is now:" in log

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("use_all_alias", [True, False])
    def test_logs_upload_and_download(
        self, setup_project, upload_or_download, use_all_alias
    ):
        """
        Set transfer verbosity and progress settings so
        maximum output is produced to test against.
        """
        subs = ["sub-11"]
        sessions = ["ses-123"]

        test_utils.make_and_check_local_project_folders(
            setup_project,
            subs,
            sessions,
            "all",
        )

        setup_project.update_config("show_transfer_progress", False)
        setup_project.update_config("transfer_verbosity", "vv")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(
            setup_project,
            upload_or_download,
            use_all_alias,
        )
        self.delete_log_files(setup_project.cfg.logging_path)

        transfer_function() if use_all_alias else transfer_function(
            "all", "all", "all"
        )

        log = self.read_log_file(setup_project.cfg.logging_path)

        suffix = "_all" if use_all_alias else ""

        assert (
            f"Starting logging for command {upload_or_download}{suffix}" in log
        )

        if use_all_alias:
            assert (
                "VariablesState:\nlocals: {'dry_run': False}\ncfg: {'local_path':"
                in log
            )
        else:
            assert (
                "VariablesState:\nlocals: {'sub_names': 'all', 'ses_names': 'all', 'datatype': 'all', 'dry_run': False, 'init_log': True}\ncfg: {'local_path': "
                in log
            )

        # 'remote' here is rclone terminology
        assert "Creating backend with remote" in log

        assert "Using config file from" in log
        assert "Local file system at" in log
        assert """ "--include" "sub-11/histology/**" """ in log
        assert """/test_logging/central/rawdata""" in log
        assert "Waiting for checks to finish" in log

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_logs_upload_and_download_folder_or_file(
        self, setup_project, upload_or_download
    ):
        """
        Set transfer verbosity and progress settings so
        maximum output is produced to test against.
        """
        test_utils.make_and_check_local_project_folders(
            setup_project,
            subs=["sub-001"],
            sessions=["ses-001"],
            datatype="all",
        )

        setup_project.update_config("show_transfer_progress", False)
        setup_project.update_config("transfer_verbosity", "vv")

        test_utils.handle_upload_or_download(
            setup_project,
            upload_or_download,
        )
        self.delete_log_files(setup_project.cfg.logging_path)

        if upload_or_download == "upload":
            setup_project.upload_specific_folder_or_file("sub-001/ses-001")
        else:
            setup_project.download_specific_folder_or_file("sub-001/ses-001")

        log = self.read_log_file(setup_project.cfg.logging_path)

        assert (
            f"Starting logging for command {upload_or_download}_specific_folder_or_file"
            in log
        )
        assert (
            "\n\nVariablesState:\nlocals: {'filepath': 'sub-001/ses-001', "
            "'dry_run': False}\ncfg: {'local_path':" in log
        )
        assert """sub-001/ses-001"]""" in log
        assert "Using config file from" in log
        assert "Waiting for checks to finish" in log

    # ----------------------------------------------------------------------------------------------------------
    # Check errors propagate
    # ----------------------------------------------------------------------------------------------------------

    def test_logs_check_update_config_error(self, setup_project):
        """"""
        with pytest.raises(BaseException):
            setup_project.update_config("connection_method", "ssh")

        log = self.read_log_file(setup_project.cfg.logging_path)

        assert (
            "'central_host_id' and 'central_host_username' are "
            "required if 'connection_method' is 'ssh'." in log
        )

        assert (
            "\n\nVariablesState:\nlocals: {'option_key': 'connection_method', 'new_info': 'ssh', 'store_logs_in_temp_folder': False}\ncfg: {'local_path':"
            in log
        )
        assert "connection_method was not updated" in log

    def test_logs_bad_make_sub_folders_error(self, setup_project):
        """"""
        setup_project.make_sub_folders("sub-001", datatype="all")
        self.delete_log_files(setup_project.cfg.logging_path)

        with pytest.raises(BaseException):
            setup_project.make_sub_folders("sub-001", datatype="all")

        log = self.read_log_file(setup_project.cfg.logging_path)

        assert (
            "Cannot make folders. The key sub-1 (possibly with leading zeros) already exists in the project"
            in log
        )

    @pytest.mark.skipif("not IS_WINDOWS")
    def test_temp_log_folder_made_make_config_file(
        self, clean_project_name, tmp_path
    ):
        """"""
        project = DataShuttle(clean_project_name)

        configs = test_utils.get_test_config_arguments_dict(tmp_path)
        configs["local_path"] = BAD_WINDOWS_FILECHAR

        with pytest.raises(BaseException):
            project.make_config_file(**configs)

        tmp_path_logs = glob.glob(str(project._temp_log_path / "*.log"))

        assert len(tmp_path_logs) == 1
        assert "make_config_file" in tmp_path_logs[0]

    def test_temp_log_folder_moved_make_config_file(
        self, clean_project_name, tmp_path
    ):
        """
        Check the logs are moved to the new logging path
        after project init for the first time.
        """
        project = DataShuttle(clean_project_name)

        configs = test_utils.get_test_config_arguments_dict(tmp_path)
        project.make_config_file(**configs)

        tmp_path_logs = glob.glob(str(project._temp_log_path / "*.log"))
        project_path_logs = glob.glob(str(project.cfg.logging_path / "*.log"))

        assert len(tmp_path_logs) == 0
        assert len(project_path_logs) == 1
        assert "make_config_file" in project_path_logs[0]

    @pytest.mark.skipif("not IS_WINDOWS")
    @pytest.mark.parametrize("supply_or_update", ["update", "supply"])
    def test_temp_log_folder_made_update_config(
        self, setup_project, supply_or_update, tmp_path
    ):
        """"""
        self.delete_log_files(setup_project.cfg.logging_path)

        # Try to set local_path to a folder that cannot be made.
        # The existing local project exists, so put the log there
        with pytest.raises(BaseException):
            self.run_supply_or_update_configs(
                setup_project, supply_or_update, BAD_WINDOWS_FILECHAR, tmp_path
            )

        tmp_path_logs = glob.glob(str(setup_project._temp_log_path / "*.log"))
        orig_local_path_logs = glob.glob(
            str(setup_project.cfg.logging_path / "*.log")
        )

        assert len(tmp_path_logs) == 0
        assert len(orig_local_path_logs) == 1
        self.delete_log_files(setup_project.cfg.logging_path)

        # Now change the local_path to something that doesn't exist.
        # Also, the new path cannot be made. In this case store the logs
        # in the temp log file.
        setup_project.cfg["local_path"] = Path("folder_that_does_not_exist")

        with pytest.raises(BaseException):
            self.run_supply_or_update_configs(
                setup_project, supply_or_update, BAD_WINDOWS_FILECHAR, tmp_path
            )

        tmp_path_logs = glob.glob(str(setup_project._temp_log_path / "*.log"))
        orig_local_path_logs = glob.glob(
            str(setup_project.cfg.logging_path / "*.log")
        )

        assert len(tmp_path_logs) == 1
        assert len(orig_local_path_logs) == 0

    @pytest.mark.parametrize("supply_or_update", ["update", "supply"])
    def test_temp_log_folder_moved(
        self, setup_project, supply_or_update, tmp_path
    ):
        """
        Now set the existing project path to one that does not
        exist but the new one to a project that does - and check
        logs are moved to new project.
        """
        setup_project.cfg["local_path"] = Path("folder_that_does_not_exist")
        new_log_path = setup_project.cfg.logging_path / "new_logs"

        self.run_supply_or_update_configs(
            setup_project,
            supply_or_update,
            new_local_path=new_log_path.as_posix(),
            tmp_path=tmp_path,
        )

        tmp_path_logs = glob.glob(str(setup_project._temp_log_path / "*.log"))
        new_path_logs = glob.glob(
            str(new_log_path / ".datashuttle" / "logs" / "*.log")
        )

        assert len(tmp_path_logs) == 0
        assert len(new_path_logs) == 1

    def run_supply_or_update_configs(
        self, project, supply_or_update, new_local_path, tmp_path
    ):
        """"""
        if supply_or_update == "update":
            project.update_config("local_path", new_local_path)
        else:
            new_configs_path, _ = test_utils.make_correct_supply_config_file(
                project,
                tmp_path,
                update_configs={"key": "local_path", "value": new_local_path},
            )
            project.supply_config_file(new_configs_path, warn=False)
