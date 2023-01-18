import os
import re

import pytest
import test_utils

from datashuttle.configs.canonical_tags import tags


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
    @pytest.mark.parametrize("use_all_alias", [True, False])
    def test_transfer_empty_folder_structure(
        self,
        project,
        upload_or_download,
        use_all_alias,
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
        ) = test_utils.handle_upload_or_download(
            project, upload_or_download, use_all_alias=use_all_alias
        )

        if use_all_alias:
            transfer_function()
        else:
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
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
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
        subs = ["001", f"02{tags('to')}03"]
        sessions = [f"ses-01{tags('to')}003_{tags('datetime')}"]

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

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_wildcard_transfer(self, project, upload_or_download):
        """
        Transfer a subset of define subject and session
        and check only the expected folders are there.
        """
        subs = ["sub-hello", "sub-hullo", "sub-world"]
        sessions = [
            "001_date-20220501",
            "002_date-20220516",
            "003_date-20220601",
        ]

        project.make_sub_dir(subs, sessions, "all")

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(
            f"sub-h{tags('*')}llo",
            f"ses-{tags('*')}_date-202205{tags('*')}",
            ["ephys", "behav", "funcimg"],
        )

        transferred_subs = test_utils.glob_basenames(
            (base_path_to_check / "rawdata" / "*").as_posix()
        )
        expected_subs = ["sub-hello", "sub-hullo"]
        assert transferred_subs == ["sub-hello", "sub-hullo"]

        for sub in expected_subs:
            transferred_ses = test_utils.glob_basenames(
                (base_path_to_check / "rawdata" / sub / "*").as_posix()
            )
            assert transferred_ses == [
                "ses-001_date-20220501",
                "ses-002_date-20220516",
            ]

    @pytest.mark.parametrize("overwrite_old_files_on_transfer", [True, False])
    @pytest.mark.parametrize("show_transfer_progress", [True, False])
    @pytest.mark.parametrize("dry_run", [True, False])
    def test_rclone_options(
        self,
        project,
        overwrite_old_files_on_transfer,
        show_transfer_progress,
        dry_run,
        capsys,
    ):
        """
        When verbosity is --vv, rclone itself will output
        a list of all called arguments. Use this to check
        rclone is called with the arguments set in configs
        as expected. verbosity itself is tested in another method.
        """
        project.make_sub_dir(["sub-001"], ["ses-002"], ["behav"])

        project.update_config(
            "overwrite_old_files_on_transfer", overwrite_old_files_on_transfer
        )
        project.update_config("transfer_verbosity", "vv")
        project.update_config("show_transfer_progress", show_transfer_progress)

        test_utils.clear_capsys(capsys)
        project.upload_all(dry_run=dry_run)

        log = capsys.readouterr().out

        assert "--create-empty-src-dirs" in log

        if overwrite_old_files_on_transfer:
            assert "--ignore-existing" not in log
        else:
            assert "--ignore-existing" in log

        if show_transfer_progress:
            assert "--progress" in log
        else:
            assert "--progress" not in log

        if dry_run:
            assert "--dry-run" in log
        else:
            assert "--dry-run" not in log

    @pytest.mark.parametrize("transfer_verbosity", ["v", "vv"])
    def test_rclone_transfer_verbosity(
        self, project, transfer_verbosity, capsys
    ):
        """
        see test_rclone_options()
        """
        project.make_sub_dir(["sub-001"], ["ses-002"], ["behav"])
        project.update_config("transfer_verbosity", transfer_verbosity)

        test_utils.clear_capsys(capsys)
        project.upload_all()

        log = capsys.readouterr().out

        if transfer_verbosity == "vv":
            assert "-vv" in log
        elif transfer_verbosity == "v":
            assert "starting with parameters [" not in log and "-vv" not in log
        else:
            raise BaseException("wrong parameter passed as transfer_verbosity")
