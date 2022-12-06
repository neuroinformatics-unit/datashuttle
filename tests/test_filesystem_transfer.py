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

        test_utils.make_and_check_local_project(project, "all", subs, sessions)

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function("all", "all", "all")

        test_utils.check_directory_tree_is_correct(
            project,
            base_path_to_check,
            subs,
            sessions,
            test_utils.get_default_directory_used(),
        )

    @pytest.mark.parametrize(
        "experiment_type_to_transfer",
        [
            ["behav"],
            ["ephys"],
            ["imaging"],
            ["histology"],
            ["behav", "ephys"],
            ["ephys", "histology"],
            ["behav", "ephys", "histology"],
            ["imaging", "histology", "behav"],
            ["behav", "ephys", "imaging", "histology"],
        ],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_transfer_empty_folder_specific_experimental_data(
        self, project, upload_or_download, experiment_type_to_transfer
    ):
        """
        For the combination of experiment_type directories, make a directory
        tree with all experiment_type dirs then upload select ones,
        checking only the selected ones are uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project(project, "all", subs, sessions)

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(experiment_type_to_transfer, subs, sessions)

        test_utils.check_experiment_type_sub_ses_uploaded_correctly(
            base_path_to_check, experiment_type_to_transfer
        )

    @pytest.mark.parametrize(
        "sub_idx_to_upload", [[0], [1], [2], [0, 1], [1, 2], [0, 2], [0, 1, 2]]
    )
    @pytest.mark.parametrize(
        "experiment_type_to_transfer",
        [
            ["histology"],
            ["behav", "ephys"],
            ["imaging", "histology", "behav"],
            ["behav", "ephys", "imaging", "histology"],
        ],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload" "download"])
    def test_transfer_empty_folder_specific_subs(
        self,
        project,
        upload_or_download,
        experiment_type_to_transfer,
        sub_idx_to_upload,
    ):
        """
        Create a project folder tree with a set of subs, then
        take a subset of these subs and upload them. Check only the
        selected subs were uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project(project, "all", subs, sessions)

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        transfer_function(
            experiment_type_to_transfer, subs_to_upload, sessions
        )

        test_utils.check_experiment_type_sub_ses_uploaded_correctly(
            base_path_to_check,
            experiment_type_to_transfer,
            subs_to_upload,
        )

    @pytest.mark.parametrize(
        "ses_idx_to_upload", [[0], [1], [2], [0, 1], [1, 2], [0, 2], [0, 1, 2]]
    )
    @pytest.mark.parametrize("sub_idx_to_upload", [[0], [1, 2], [0, 1, 2]])
    @pytest.mark.parametrize(
        "experiment_type_to_transfer",
        [["ephys"], ["imaging", "histology", "behav"]],
    )
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_transfer_empty_folder_specific_ses(
        self,
        project,
        upload_or_download,
        experiment_type_to_transfer,
        sub_idx_to_upload,
        ses_idx_to_upload,
    ):
        """
        Make a project with set subs and sessions. Then select a subset of the
        sessions to upload. Check only the selected sessions were uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project(project, "all", subs, sessions)

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        ses_to_upload = [sessions[i] for i in ses_idx_to_upload]

        transfer_function(
            experiment_type_to_transfer, subs_to_upload, ses_to_upload
        )

        test_utils.check_experiment_type_sub_ses_uploaded_correctly(
            base_path_to_check,
            experiment_type_to_transfer,
            subs_to_upload,
            ses_to_upload,
        )
