import os
from os.path import join

import pytest
import test_utils


class TestFileTransfer:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """
        Create a project with default configs loaded. This makes a fresh project
        for each function, saved in the appdir path for platform independent and to
        avoid path setup on new machine.

        Ensure change dir at end of session otherwise it is not possible
        to delete project.
        """
        test_project_name = "test_filesystem_transfer"

        project = test_utils.setup_project_default_configs(
            test_project_name,
            local_path=tmp_path / test_project_name / "local",
            remote_path=tmp_path / test_project_name / "remote",
        )

        cwd = os.getcwd()
        yield project
        test_utils.teardown_project(cwd, project)

    # ----------------------------------------------------------------------------------------------------------
    # Tests
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "upload_or_download", ["upload"]
    )  # , "download"])
    def test_transfer_empty_folder_structure(
        self, project, upload_or_download
    ):
        """
        First make a project (folders only) locally. Next upload this to the remote path
        and check all folders are uploaded correctly.
        """
        subs, sessions = self.get_default_sub_sessions_to_test()

        self.make_and_check_local_project(project, "all", subs, sessions)

        transfer_function, base_path_to_check = self.handle_upload_or_download(
            project, upload_or_download
        )

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
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, "all", subs, sessions)

        transfer_function, base_path_to_check = self.handle_upload_or_download(
            project, upload_or_download
        )

        transfer_function(experiment_type_to_transfer, subs, sessions)

        self.check_experiment_type_sub_ses_uploaded_correctly(
            project, base_path_to_check, experiment_type_to_transfer
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
    @pytest.mark.parametrize(
        "upload_or_download", ["download"]
    )  # "upload" "download"
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
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, "all", subs, sessions)

        transfer_function, base_path_to_check = self.handle_upload_or_download(
            project, upload_or_download
        )

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        transfer_function(
            experiment_type_to_transfer, subs_to_upload, sessions
        )
        try:
            self.check_experiment_type_sub_ses_uploaded_correctly(
                project,
                base_path_to_check,
                experiment_type_to_transfer,
                subs_to_upload,
            )
        except:
            breakpoint()

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
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, "all", subs, sessions)

        transfer_function, base_path_to_check = self.handle_upload_or_download(
            project, upload_or_download
        )

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        ses_to_upload = [sessions[i] for i in ses_idx_to_upload]

        transfer_function(
            experiment_type_to_transfer, subs_to_upload, ses_to_upload
        )

        self.check_experiment_type_sub_ses_uploaded_correctly(
            project,
            base_path_to_check,
            experiment_type_to_transfer,
            subs_to_upload,
            ses_to_upload,
        )

    # ----------------------------------------------------------------------------------------------------------
    # Test Helers
    # ----------------------------------------------------------------------------------------------------------

    def check_experiment_type_sub_ses_uploaded_correctly(
        self,
        project,
        base_path_to_check,
        experiment_type_to_transfer,
        subs_to_upload=None,
        ses_to_upload=None,
    ):
        """
        Itereate through the project (experiment_type > ses > sub) and
        check that the directories at each level match those that are
        expected (passed in experiment / sub / ses to upload). Dirs
        are searched with wildcard glob.
        """
        experiment_names = test_utils.glob_basenames(
            join(base_path_to_check, "*")
        )
        assert experiment_names == sorted(experiment_type_to_transfer)

        if subs_to_upload:
            for experiment_type in experiment_type_to_transfer:
                sub_names = test_utils.glob_basenames(
                    join(base_path_to_check, experiment_type, "*")
                )
                assert sub_names == sorted(subs_to_upload)

                if ses_to_upload:

                    for sub in subs_to_upload:
                        ses_names = test_utils.glob_basenames(
                            join(
                                base_path_to_check,
                                experiment_type,
                                sub,
                                "*",
                            )
                        )
                        assert ses_names == sorted(ses_to_upload)

    def make_and_check_local_project(
        self, project, experiment_type, subs, sessions
    ):
        """
        Make a local project directory tree with the specified experiment_type,
        subs, sessions and check it is made successfully.
        """
        project.make_sub_dir(
            experiment_type,
            subs,
            sessions,
            test_utils.get_default_directory_used(),
        )

        test_utils.check_directory_tree_is_correct(
            project,
            project.get_local_path(),
            subs,
            sessions,
            test_utils.get_default_directory_used(),
        )

    def handle_upload_or_download(self, project, upload_or_download):
        """
        To keep things consistent and avoid the pain of writing files over SSH,
        to test download just swap the remote and local server (so things are
        still transferred from local machine to remote, but using the download function).
        """
        import copy

        local_path = copy.deepcopy(project.get_local_path())
        remote_path = copy.deepcopy(project.get_remote_path())

        if upload_or_download == "download":

            project.update_config("local_path", remote_path)
            project.update_config("remote_path", local_path)

            transfer_function = project.download_data

        else:
            transfer_function = project.upload_data

        return transfer_function, remote_path

    def get_default_sub_sessions_to_test(self):
        """
        Cannonial subs / sessions for these tests
        """
        subs = ["sub-001", "sub-002", "sub-003"]
        sessions = ["ses-001-23092022-13h50s", "ses-002", "ses-003"]
        return subs, sessions
