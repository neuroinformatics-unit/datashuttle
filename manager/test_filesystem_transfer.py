import os
from os.path import join

import pytest

from manager import test_utils

# NOTE, these tests will delete all folders in the local and remote path
# (as these are dedicated for testing). But in theory this could cause
# problems if mis-understood and files are deleted without intention. worth discussing.
# a hook before tests are run to check nothing is in the folders specified in configs? probs work best

# data directory - use pytest config file
TEST_PROJECT_NAME = "test_filesystem_transfer"
LOCAL_PATH = (
    r"C:\data\project_manager\test_transfer_data\test_filesystem_transfer"
)
REMOTE_PATH = r"Z:\manager\test_filesystem_transfer"


class TestFileTransfer:
    @pytest.fixture(scope="function")
    def project(test):
        """
        Create a project with default configs loaded. This makes a fresh project
        for each function, saved in the appdir path for platform independent and to
        avoid path setup on new machine.

        Ensure change dir at end of session otherwise it is not possible
        to delete project.
        """
        project = test_utils.setup_project_default_configs(
            TEST_PROJECT_NAME,
            override_local_and_remote_paths=[LOCAL_PATH, REMOTE_PATH],
        )

        cwd = os.getcwd()
        yield project
        test_utils.teardown_project(cwd, project)

    def make_and_check_local_project(self, project, subs, sessions):
        """"""
        project.make_sub_dir(
            "all", subs, sessions, test_utils.get_default_directory_used()
        )

        test_utils.check_directory_tree_is_made(
            project,
            project.get_local_path(),
            subs,
            sessions,
            test_utils.get_default_directory_used(),
        )

    def get_default_sub_sessions_to_test(self):
        subs = ["sub-001", "sub-002", "sub-003"]
        sessions = ["ses-001-23092022-13h50s", "ses-002", "ses-003"]
        return subs, sessions

    def test_upload_empty_folder_structure(self, project):
        """"""
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, subs, sessions)

        project.upload_data("all", "all", "all")

        test_utils.check_directory_tree_is_made(
            project,
            project.get_remote_path(),
            subs,
            sessions,
            test_utils.get_default_directory_used(),
        )

    @pytest.mark.parametrize(
        "experiment_type_to_upload",
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
    def test_upload_empty_folder_specific_experimental_data(
        self, project, experiment_type_to_upload
    ):
        """"""
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, subs, sessions)

        project.upload_data(experiment_type_to_upload, subs, sessions)

        self.check_experiment_type_sub_ses_uploaded_correctly(
            project, experiment_type_to_upload
        )

    @pytest.mark.parametrize(
        "sub_idx_to_upload", [[0], [1], [2], [0, 1], [1, 2], [0, 2], [0, 1, 2]]
    )
    @pytest.mark.parametrize(
        "experiment_type_to_upload",
        [
            ["histology"],
            ["behav", "ephys"],
            ["imaging", "histology", "behav"],
            ["behav", "ephys", "imaging", "histology"],
        ],
    )
    def test_upload_empty_folder_specific_subs(
        self,
        project,
        experiment_type_to_upload,
        sub_idx_to_upload,
    ):
        """"""
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, subs, sessions)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        project.upload_data(
            experiment_type_to_upload, subs_to_upload, sessions
        )

        self.check_experiment_type_sub_ses_uploaded_correctly(
            project, experiment_type_to_upload, subs_to_upload
        )

    @pytest.mark.parametrize(
        "ses_idx_to_upload", [[0], [1], [2], [0, 1], [1, 2], [0, 2], [0, 1, 2]]
    )
    @pytest.mark.parametrize("sub_idx_to_upload", [[0], [1, 2], [0, 1, 2]])
    @pytest.mark.parametrize(
        "experiment_type_to_upload",
        [["ephys"], ["imaging", "histology", "behav"]],
    )
    def test_upload_empty_folder_specific_ses(
        self,
        project,
        experiment_type_to_upload,
        sub_idx_to_upload,
        ses_idx_to_upload,
    ):
        """"""
        subs, sessions = self.get_default_sub_sessions_to_test()
        self.make_and_check_local_project(project, subs, sessions)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        ses_to_upload = [sessions[i] for i in ses_idx_to_upload]

        project.upload_data(
            experiment_type_to_upload, subs_to_upload, ses_to_upload
        )

        self.check_experiment_type_sub_ses_uploaded_correctly(
            project, experiment_type_to_upload, subs_to_upload, ses_to_upload
        )

    def check_experiment_type_sub_ses_uploaded_correctly(
        self,
        project,
        experiment_type_to_upload,
        subs_to_upload=None,
        ses_to_upload=None,
    ):
        """"""
        experiment_names = test_utils.glob_basenames(
            join(project.get_remote_path(), "*")
        )
        assert experiment_names == sorted(experiment_type_to_upload)

        if subs_to_upload:
            for experiment_type in experiment_type_to_upload:
                sub_names = test_utils.glob_basenames(
                    join(project.get_remote_path(), experiment_type, "*")
                )
                assert sub_names == sorted(subs_to_upload)

                if ses_to_upload:
                    for sub in subs_to_upload:
                        ses_names = test_utils.glob_basenames(
                            join(
                                project.get_remote_path(),
                                experiment_type,
                                sub,
                                "*",
                            )
                        )
                        assert ses_names == sorted(ses_to_upload)
