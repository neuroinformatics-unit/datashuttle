import os
import re

import pytest
import test_utils


class TestFileTransfer:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """
        Create a project with default configs loaded.
        This makes a fresh project for each function,
        saved in the appdir path for platform independent
        and to avoid path setup on new machine.

        Ensure change dir at end of session otherwise it
        is not possible to delete project.
        """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_filesystem_transfer"
        project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )
        yield project
        test_utils.teardown_project(cwd, project)

    # ----------------------------------------------------------------------------------------------------------
    # Tests
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_transfer_empty_folder_structure(
        self, project, upload_or_download
    ):
        """
        First make a project (folders only) locally.
        Next upload this to the remote path
        and check all folders are uploaded correctly.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project(project, subs, sessions, "all")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function("all", "all", "all")

        test_utils.check_directory_tree_is_correct(
            project,
            os.path.join(base_path_to_check, project._top_level_dir_name),
            subs,
            sessions,
            test_utils.get_default_directory_used(),
        )

    @pytest.mark.parametrize(
        "data_type_to_transfer",
        [
            ["behav"],
            ["ephys"],
            ["funcimg"],
            ["histology"],
            ["behav", "ephys"],
            ["ephys", "histology"],
            ["behav", "ephys", "histology"],
            ["funcimg", "histology", "behav"],
            ["behav", "ephys", "funcimg", "histology"],
        ],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload"])  # "download"
    def test_transfer_empty_folder_specific_dataal_data(
        self, project, upload_or_download, data_type_to_transfer
    ):
        """
        For the combination of data_type directories, make a directory
        tree with all data_type dirs then upload select ones,
        checking only the selected ones are uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project(project, subs, sessions, "all")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(subs, sessions, data_type_to_transfer)

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            os.path.join(base_path_to_check, project._top_level_dir_name),
            data_type_to_transfer,
            subs,
            sessions,
        )

    @pytest.mark.parametrize(
        "sub_idx_to_upload", [[0], [1], [2], [0, 1], [1, 2], [0, 2], [0, 1, 2]]
    )
    @pytest.mark.parametrize(
        "data_type_to_transfer",
        [
            ["histology"],
            ["behav", "ephys"],
            ["funcimg", "histology", "behav"],
            ["behav", "ephys", "funcimg", "histology"],
        ],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload" "download"])
    def test_transfer_empty_folder_specific_subs(
        self,
        project,
        upload_or_download,
        data_type_to_transfer,
        sub_idx_to_upload,
    ):
        """
        Create a project folder tree with a set of subs, then
        take a subset of these subs and upload them. Check only the
        selected subs were uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project(project, subs, sessions, "all")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        transfer_function(subs_to_upload, sessions, data_type_to_transfer)

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            os.path.join(base_path_to_check, project._top_level_dir_name),
            data_type_to_transfer,
            subs_to_upload,
        )

    @pytest.mark.parametrize(
        "ses_idx_to_upload", [[0], [1], [2], [0, 1], [1, 2], [0, 2], [0, 1, 2]]
    )
    @pytest.mark.parametrize("sub_idx_to_upload", [[0], [1, 2], [0, 1, 2]])
    @pytest.mark.parametrize(
        "data_type_to_transfer",
        [["ephys"], ["funcimg", "histology", "behav"]],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_transfer_empty_folder_specific_ses(
        self,
        project,
        upload_or_download,
        data_type_to_transfer,
        sub_idx_to_upload,
        ses_idx_to_upload,
    ):
        """
        Make a project with set subs and sessions. Then select a subset of the
        sessions to upload. Check only the selected sessions were uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project(project, subs, sessions, "all")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        ses_to_upload = [sessions[i] for i in ses_idx_to_upload]

        transfer_function(subs_to_upload, ses_to_upload, data_type_to_transfer)

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            os.path.join(base_path_to_check, project._top_level_dir_name),
            data_type_to_transfer,
            subs_to_upload,
            ses_to_upload,
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_transfer_with_keyword_parameters(
        self, project, upload_or_download
    ):
        """
        Test the @TO@ keyword is accepted properly when making a session and
        transferring it. First pass @TO@-formatted sub and sessions to
        make_sub_dir. Then transfer the files (upload or download).

        Finally, check the expected formatting on the subject and session
        is observed on the created and transferred file paths.
        """
        subs = ["001", "02@TO@03"]
        sessions = ["ses-01@TO@003_@DATETIME@"]

        project.make_sub_dir(subs, sessions, "all")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(subs, "all", "all")

        for base_local in [
            project.cfg["local_path"],
            project.cfg["remote_path"],
        ]:

            for sub in ["sub-001", "sub-02", "sub-03"]:

                sessions_in_path = test_utils.glob_basenames(
                    (base_local / "rawdata" / sub / "ses*").as_posix()
                )

                datetime_regexp = r"date-\d\d\d\d\d\d\d\d_time-\d\d\d\d\d\d"

                assert re.match(
                    "ses-001_" + datetime_regexp, sessions_in_path[0]
                )
                assert re.match(
                    "ses-002_" + datetime_regexp, sessions_in_path[1]
                )
                assert re.match(
                    "ses-003_" + datetime_regexp, sessions_in_path[2]
                )
