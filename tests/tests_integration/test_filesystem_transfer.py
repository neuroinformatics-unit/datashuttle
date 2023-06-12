import os
import re
from pathlib import Path

import pytest
import test_utils

from datashuttle.configs import canonical_folders
from datashuttle.configs.canonical_tags import tags


class TestFileTransfer:
    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """
        Create a project with default configs loaded.
        This makes a fresh project for each function,
        saved in the appdir path for platform independent
        and to avoid path setup on new machine.

        Ensure change folder at end of session otherwise it
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
        Next upload this to the central path
        and check all folders are uploaded correctly.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        test_utils.make_and_check_local_project_folders(
            project, subs, sessions, "all"
        )

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

        test_utils.check_folder_tree_is_correct(
            project,
            os.path.join(base_path_to_check, project.cfg.top_level_folder),
            subs,
            sessions,
            test_utils.get_default_folder_used(),
        )

    def test_empty_folder_is_not_transferred(self, project):
        project.make_sub_folders("sub-001")
        project.upload_all()
        assert not (project.cfg["central_path"] / "sub-001").is_dir()

    @pytest.mark.parametrize(
        "folder_name", canonical_folders.get_top_level_folders()
    )
    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("use_all_alias", [True, False])
    def test_transfer_across_top_level_folders(
        self, project, folder_name, upload_or_download, use_all_alias
    ):
        """
        For each possible top level folder (e.g. rawdata, derivatives)
        (parametrized) create a folder tree in every top-level folder,
        then transfer using upload / download and
        upload_all / download_all that only the working top-level folder
        is transferred.
        """
        project.set_top_level_folder(folder_name)
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        for making_folder_name in canonical_folders.get_top_level_folders():
            project.cfg.top_level_folder = making_folder_name
            test_utils.make_and_check_local_project_folders(
                project, subs, sessions, "all", folder_name=making_folder_name
            )
        project.cfg.top_level_folder = folder_name

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

        full_base_path_to_check = (
            base_path_to_check / project.cfg.top_level_folder
        )

        test_utils.check_working_top_level_folder_only_exists(
            folder_name, project, full_base_path_to_check, subs, sessions
        )

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_transfer_all_top_level_folders(self, project, upload_or_download):
        """ """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()

        for folder_name in canonical_folders.get_top_level_folders():
            project.set_top_level_folder(folder_name)

            test_utils.make_and_check_local_project_folders(
                project, subs, sessions, "all", folder_name=folder_name
            )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(
            project, upload_or_download, transfer_entire_project=True
        )

        transfer_function()

        for folder_name in canonical_folders.get_top_level_folders():
            project.set_top_level_folder(folder_name)
            test_utils.check_folder_tree_is_correct(
                project,
                os.path.join(base_path_to_check, project.cfg.top_level_folder),
                subs,
                sessions,
                test_utils.get_default_folder_used(),
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
        For the combination of data_type folders, make a folder
        tree with all data_type folders then upload select ones,
        checking only the selected ones are uploaded.
        """
        subs, sessions = test_utils.get_default_sub_sessions_to_test()
        test_utils.make_and_check_local_project_folders(
            project, subs, sessions, "all"
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(subs, sessions, data_type_to_transfer)

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            os.path.join(base_path_to_check, project.cfg.top_level_folder),
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
        test_utils.make_and_check_local_project_folders(
            project, subs, sessions, "all"
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        transfer_function(subs_to_upload, sessions, data_type_to_transfer)

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            os.path.join(base_path_to_check, project.cfg.top_level_folder),
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
        test_utils.make_and_check_local_project_folders(
            project, subs, sessions, "all"
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        subs_to_upload = [subs[i] for i in sub_idx_to_upload]
        ses_to_upload = [sessions[i] for i in ses_idx_to_upload]

        transfer_function(subs_to_upload, ses_to_upload, data_type_to_transfer)

        test_utils.check_data_type_sub_ses_uploaded_correctly(
            os.path.join(base_path_to_check, project.cfg.top_level_folder),
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
        make_sub_folders. Then transfer the files (upload or download).

        Finally, check the expected formatting on the subject and session
        is observed on the created and transferred file paths.
        """
        subs = ["001", f"02{tags('to')}03"]
        sessions = [f"ses-01{tags('to')}003_{tags('datetime')}"]

        test_utils.make_local_folders_with_files_in(
            project, subs, sessions, "all"
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(subs, "all", "all")

        for base_local in [
            project.cfg["local_path"],
            project.cfg["central_path"],
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
        subs = ["sub-389", "sub-989", "sub-445"]
        sessions = [
            "001_date-20220501",
            "002_date-20220516",
            "003_date-20220601",
        ]

        test_utils.make_local_folders_with_files_in(
            project, subs, sessions, "all"
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(project, upload_or_download)

        transfer_function(
            f"sub-{tags('*')}89",
            f"ses-{tags('*')}_date-202205{tags('*')}",
            ["ephys", "behav", "funcimg"],
        )

        transferred_subs = test_utils.glob_basenames(
            (base_path_to_check / "rawdata" / "*").as_posix()
        )
        expected_subs = ["sub-389", "sub-989"]
        assert transferred_subs == expected_subs

        for sub in expected_subs:
            transferred_ses = test_utils.glob_basenames(
                (base_path_to_check / "rawdata" / sub / "*").as_posix()
            )
            assert transferred_ses == [
                "ses-001_date-20220501",
                "ses-002_date-20220516",
            ]

    @pytest.mark.parametrize("overwrite_old_files", [True, False])
    @pytest.mark.parametrize("show_transfer_progress", [True, False])
    @pytest.mark.parametrize("dry_run", [True, False])
    def test_rclone_options(
        self,
        project,
        overwrite_old_files,
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
        test_utils.make_local_folders_with_files_in(
            project, ["sub-001"], ["ses-002"], ["behav"]
        )

        project.update_config("overwrite_old_files", overwrite_old_files)
        project.update_config("transfer_verbosity", "vv")
        project.update_config("show_transfer_progress", show_transfer_progress)

        test_utils.clear_capsys(capsys)
        project.upload_all(dry_run=dry_run)

        log = capsys.readouterr().out

        if overwrite_old_files:
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
        project.make_sub_folders(["sub-001"], ["ses-002"], ["behav"])
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

    @pytest.mark.parametrize("overwrite_old_files", [True, False])
    def test_rclone_overwrite_modified_file(
        self, project, overwrite_old_files
    ):
        """
        Test how rclone deals with existing files. In datashuttle
        if project.cfg["overwrite_old_files"] is on,
        files will be replaced with newer versions. Alternatively,
        if this is off, files will never be overwritten even if
        the version in source is newer than target.
        """
        path_to_test_file = (
            Path("rawdata") / "sub-001" / "histology" / "test_file.txt"
        )

        project.make_sub_folders("sub-001")
        local_test_file_path = project.cfg["local_path"] / path_to_test_file
        central_test_file_path = (
            project.cfg["central_path"] / path_to_test_file
        )

        # Write a local file and transfer
        test_utils.write_file(local_test_file_path, contents="first edit")

        time_written = os.path.getatime(local_test_file_path)

        if overwrite_old_files:
            project.update_config("overwrite_old_files", True)

        project.upload_all()

        # Update the file and transfer and transfer again
        test_utils.write_file(
            local_test_file_path, contents=" second edit", append=True
        )

        assert time_written < os.path.getatime(local_test_file_path)

        project.upload_all()

        central_contents = test_utils.read_file(central_test_file_path)

        if overwrite_old_files:
            assert central_contents == ["first edit second edit"]
        else:
            assert central_contents == ["first edit"]

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    @pytest.mark.parametrize("transfer_file", [True, False])
    @pytest.mark.parametrize("full_path", [True, False])
    def test_specific_file_or_folder(
        self, project, transfer_file, full_path, upload_or_download
    ):
        """
        Test upload_specific_folder_or_file() and download_specific_folder_or_file().

        This test has a few different parameterisations. It tests
        1) transfer_file : this transfers a file or folder. if transferring
           a folder, all contents are transferred with /** wildcard.
        2) full path : the functions can accept full path or path
           relative to rawdata/ . Test both these instances
        3) upload_or_download : Test the direction. As it is more convenient
           to  make all test project file in local_path then swap the paths
           if downloading, this is done here (see
           test_utils.swap_local_and_central_paths()) for details.

        Make a project with two different files (just to
        ensure non-target files are not transferred). Transfer
        a single file or the folder containing the file. Check that
        the transferred folders and no others were transferred.
        """
        (
            path_to_test_file_behav,
            path_to_test_file_ephys,
        ) = self.setup_specific_file_or_folder_files(project)

        if upload_or_download == "upload":
            transfer_function = project.upload_specific_folder_or_file
            transfer_from = "local_path"
            transfer_to = "central_path"
        else:
            transfer_function = project.download_specific_folder_or_file
            transfer_from = "central_path"
            transfer_to = "local_path"
            test_utils.swap_local_and_central_paths(project)

        if transfer_file:
            to_transfer = path_to_test_file_behav
            formatted_to_transfer = to_transfer
        else:
            to_transfer = path_to_test_file_ephys
            formatted_to_transfer = to_transfer.parents[0] / "**"

        if full_path:
            transfer_function(
                project.cfg[transfer_from] / formatted_to_transfer
            )
        else:
            transfer_function(Path(*formatted_to_transfer.parts[1:]))

        transferred_files = [
            path_
            for path_ in project.cfg[transfer_to].glob("**/*")
            if ".datashuttle" not in str(path_)
        ]
        to_test_against = [
            project.cfg[transfer_to] / path_
            for path_ in reversed(to_transfer.parents)
        ][1:] + [project.cfg[transfer_to] / to_transfer]

        assert transferred_files == to_test_against

    def setup_specific_file_or_folder_files(self, project):
        """ """
        project.make_sub_folders(["sub-001", "sub-002"], "ses-003")

        path_to_test_file_behav = (
            Path("rawdata")
            / "sub-002"
            / "ses-003"
            / "behav"
            / "behav_test_file.txt"
        )

        path_to_test_file_ephys = (
            Path("rawdata")
            / "sub-002"
            / "ses-003"
            / "ephys"
            / "ephys_test_file.txt"
        )

        test_utils.write_file(
            project.cfg["local_path"] / path_to_test_file_behav
        )
        test_utils.write_file(
            project.cfg["local_path"] / path_to_test_file_ephys
        )

        return path_to_test_file_behav, path_to_test_file_ephys
