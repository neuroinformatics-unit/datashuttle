import datetime
import re
import shutil
from os.path import join

import pytest
import test_utils
from base import BaseTest

from datashuttle.configs import canonical_folders
from datashuttle.configs.canonical_tags import tags


class TestMakeFolders(BaseTest):
    def test_duplicate_ses_or_sub_key_value_pair(self, project):
        """
        Test the check that if a duplicate key is attempt to be made
        when making a folder e.g. sub-001 exists, then make sub-001_id-123.
        After this check, make a folder that can be made (e.g. sub-003)
        just to make sure it does not raise error.

        Then, within an already made subject, try and make a session
        with a ses that already exists and check.
        """
        # Check trying to make sub only
        subs = ["sub-001_id-123", "sub-002_id-124"]
        project.make_folders(subs)

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001_id-125")

        assert (
            str(e.value) == "Cannot make folders. "
            "The key sub-1 (possibly with leading zeros) "
            "already exists in the project"
        )

        project.make_folders("sub-003")

        # check try and make ses within a sub
        sessions = ["ses-001_date-1605", "ses-002_date-1606"]
        project.make_folders(subs, sessions)

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001_id-123", "ses-002_date-1607")

        assert (
            str(e.value)
            == "Cannot make folders. The key ses-2 for sub-001_id-123 "
            "(possibly with leading zeros) already exists "
            "in the project"
        )

        project.make_folders("sub-001", "ses-003")

    def test_duplicate_sub_and_ses_num_leading_zeros(self, project):
        """
        Very similar to test_duplicate_ses_or_sub_key_value_pair(),
        but explicitly check that error is raised if the same
        number is used with different number of leading zeros.
        """
        project.make_folders("sub-001")

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-1")

        assert (
            str(e.value) == "Cannot make folders. The key sub-1 "
            "(possibly with leading zeros) already exists "
            "in the project"
        )

        project.make_folders("sub-001", "ses-3")

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001", "ses-003")

        assert (
            str(e.value) == "Cannot make folders. The key ses-3 for"
            " sub-001 (possibly with leading zeros) "
            "already exists in the project"
        )

    def test_generate_folders_default_ses(self, project):
        """
        Make a subject folders with full tree. Don't specify
        session name (it will default to no sessions).

        Check that the folder tree is created correctly. Pass
        a dict that indicates if each subfolder is used (to avoid
        circular testing from the project itself).
        """
        subs = ["11", "sub-002", "30303"]

        project.make_folders(subs)

        test_utils.check_folder_tree_is_correct(
            project,
            base_folder=test_utils.get_top_level_folder_path(project),
            subs=["sub-11", "sub-002", "sub-30303"],
            sessions=[],
            folder_used=test_utils.get_all_folders_used(),
        )

    def test_explicitly_session_list(self, project):
        """
        Perform an alternative test where the output is tested explicitly.
        This is some redundancy to ensure tests are working correctly and
        make explicit the expected folder tree.

        Note for new folders, this will have to be manually updated.
        This is highlighted in an assert in check_and_cd_folder()
        """
        subs = ["sub-001", "sub-002"]
        sessions = ["ses-001", "50432"]
        project.make_folders(subs, sessions)
        base_folder = test_utils.get_top_level_folder_path(project)

        for sub in subs:
            for ses in ["ses-001", "ses-50432"]:
                test_utils.check_and_cd_folder(
                    join(base_folder, sub, ses, "ephys")
                )
                test_utils.check_and_cd_folder(
                    join(
                        base_folder,
                        sub,
                        ses,
                        "behav",
                    )
                )
                test_utils.check_and_cd_folder(
                    join(base_folder, sub, ses, "funcimg")
                )
                test_utils.check_and_cd_folder(
                    join(base_folder, sub, "histology")
                )

    @pytest.mark.parametrize("behav", [True, False])
    @pytest.mark.parametrize("ephys", [True, False])
    @pytest.mark.parametrize("funcimg", [True, False])
    @pytest.mark.parametrize("histology", [True, False])
    def test_every_datatype_passed(
        self, project, behav, ephys, funcimg, histology
    ):
        """
        Check every combination of data type used and ensure only the
        correct ones are made.

        NOTE: This test could be refactored to reduce code reuse.
        """
        datatypes_to_make = []
        if behav:
            datatypes_to_make.append("behav")
        if ephys:
            datatypes_to_make.append("ephys")
        if funcimg:
            datatypes_to_make.append("funcimg")
        if histology:
            datatypes_to_make.append("histology")

        # Make folder tree
        subs = ["sub-001", "sub-002"]
        sessions = ["ses-001", "ses-002"]

        project.make_sub_folders(subs, sessions, datatypes_to_make)

        # Check folder tree is not made but all others are
        test_utils.check_folder_tree_is_correct(
            project,
            base_folder=test_utils.get_top_level_folder_path(project),
            subs=subs,
            sessions=sessions,
            folder_used={
                "behav": behav,
                "ephys": ephys,
                "funcimg": funcimg,
                "histology": histology,
            },
        )

    def test_custom_folder_names(self, project):
        """
        Change folder names to custom (non-default) and
        ensure they are made correctly.
        """
        # Change folder names to custom names
        project.cfg.datatype_folders["ephys"].name = "change_ephys"
        project.cfg.datatype_folders["behav"].name = "change_behav"
        project.cfg.datatype_folders["histology"].name = "change_histology"
        project.cfg.datatype_folders["funcimg"].name = "change_funcimg"

        # Make the folders
        sub = "sub-001"
        ses = "ses-001"
        project.make_folders(sub, ses)

        # Check the folders were not made / made.
        base_folder = test_utils.get_top_level_folder_path(project)
        test_utils.check_and_cd_folder(
            join(
                base_folder,
                sub,
                ses,
                "change_ephys",
            )
        )
        test_utils.check_and_cd_folder(
            join(base_folder, sub, ses, "change_behav")
        )
        test_utils.check_and_cd_folder(
            join(base_folder, sub, ses, "change_funcimg")
        )

        test_utils.check_and_cd_folder(
            join(base_folder, sub, "change_histology")
        )

    @pytest.mark.parametrize(
        "files_to_test",
        [
            ["all"],
            ["ephys", "behav"],
            ["ephys", "behav", "histology"],
            ["ephys", "behav", "histology", "funcimg"],
            ["funcimg", "ephys"],
            ["funcimg"],
        ],
    )
    def test_datatypes_subsection(self, project, files_to_test):
        """
        Check that combinations of datatypes passed to make file folder
        make the correct combination of datatypes.

        Note this will fail when new top level folders are added, and should be
        updated.
        """
        sub = "sub-001"
        ses = "ses-001"
        project.make_folders(sub, ses, files_to_test)

        base_folder = test_utils.get_top_level_folder_path(project)

        # Check at the subject level
        sub_file_names = test_utils.glob_basenames(
            join(base_folder, sub, "*"),
            exclude=ses,
        )
        if "histology" in files_to_test:
            assert "histology" in sub_file_names
            files_to_test.remove("histology")

        # Check at the session level
        ses_file_names = test_utils.glob_basenames(
            join(base_folder, sub, ses, "*"),
            exclude=ses,
        )

        if files_to_test == ["all"]:
            assert ses_file_names == sorted(["ephys", "behav", "funcimg"])
        else:
            assert ses_file_names == sorted(files_to_test)

    def test_date_flags_in_session(self, project):
        """
        Check that @DATE@ is converted into current date
        in generated folder names
        """
        date, time_ = self.get_formatted_date_and_time()

        project.make_folders(
            ["sub-001", "sub-002"],
            [f"ses-001_{tags('date')}", f"002_{tags('date')}"],
            "ephys",
        )

        ses_names = test_utils.glob_basenames(
            join(test_utils.get_top_level_folder_path(project), "**", "ses-*"),
            recursive=True,
        )

        assert all([date in name for name in ses_names])
        assert all([tags("date") not in name for name in ses_names])

    def test_datetime_flag_in_session(self, project):
        """
        Check that @DATETIME@ is converted to datetime
        in generated folder names
        """
        date, time_ = self.get_formatted_date_and_time()

        project.make_folders(
            ["sub-001", "sub-002"],
            [f"ses-001_{tags('datetime')}", f"002_{tags('datetime')}"],
            "ephys",
        )

        ses_names = test_utils.glob_basenames(
            join(test_utils.get_top_level_folder_path(project), "**", "ses-*"),
            recursive=True,
        )

        # Convert the minutes to regexp as could change during test runtime
        regexp_time = r"\d{6}"
        datetime_regexp = f"datetime-{date}T{regexp_time}"

        assert all([re.search(datetime_regexp, name) for name in ses_names])
        assert all([tags("time") not in name for name in ses_names])

    # ----------------------------------------------------------------------------------------------------------
    # Test Make Folders in Different Top Level Folders
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "folder_name", canonical_folders.get_top_level_folders()
    )
    def test_all_top_level_folders(self, project, folder_name):
        """
        Check that when switching the top level folder (e.g. rawdata, derivatives)
        new folders are made in the correct folder. The code that underpins this
        is very simple (all the path for folder creation / transfer is determined
        only by project.cfg.top_level_folder. Therefore if these tests pass,
        any test that passes for rawdata (all other tests are for rawdata) should
        pass for all top-level folders.
        """
        project.cfg.top_level_folder = folder_name

        subs = ["sub-001", "sub-2"]
        sessions = ["ses-001", "ses-03"]

        project.make_folders(subs, sessions)

        # Check folder tree is made in the desired top level folder
        test_utils.check_working_top_level_folder_only_exists(
            folder_name,
            project,
            project.cfg["local_path"] / folder_name,
            subs,
            sessions,
        )

    # ----------------------------------------------------------------------------------------------------------
    # Test get next subject / session numbers
    # ----------------------------------------------------------------------------------

    def test_get_next_sub_number(self, project):
        """
        Test that the next subject number is suggested correctly.
        This takes the union of subjects available in the local and
        central repository. As such test the case where either are
        empty, or when they have different subjects in.
        """
        # Create local folders, central is empty
        test_utils.make_local_folders_with_files_in(
            project, ["001", "002", "003"]
        )

        new_num, old_num = project.get_next_sub_number()

        assert new_num == 4
        assert old_num == 3

        # Upload to central, now local and central folders match
        project.upload_all()
        new_num, old_num = project.get_next_sub_number()
        assert new_num == 4
        assert old_num == 3

        # Delete subject folders from local
        folders_to_del = list(
            (project.cfg["local_path"] / "rawdata").glob("sub-*")
        )
        for path_ in folders_to_del:
            shutil.rmtree(path_)  # this doesn't work with map or listcomp

        new_num, old_num = project.get_next_sub_number()
        assert new_num == 4
        assert old_num == 3

        # Add large-sub num folders to local and check all are detected.
        project.make_folders(["004", "005"])
        new_num, old_num = project.get_next_sub_number()
        assert new_num == 6
        assert old_num == 5

    def test_get_next_ses_number(self, project):
        """
        Almost identical to test_get_next_sub_number() but with calls
        for searching sessions. This could be combined with
        above but reduces readability, so leave with some duplication.
        """
        sub = "sub-3"
        test_utils.make_local_folders_with_files_in(
            project, sub, ["001", "002", "003"]
        )
        new_num, old_num = project.get_next_sub_number()

        assert new_num == 4
        assert old_num == 3

        project.upload_all()
        new_num, old_num = project.get_next_ses_number(sub)
        assert new_num == 4
        assert old_num == 3

        folders_to_del = list(
            (project.cfg["local_path"] / "rawdata" / sub).glob("ses-*")
        )
        for path_ in folders_to_del:
            shutil.rmtree(path_)  # this doesn't work with map or listcomp

        new_num, old_num = project.get_next_ses_number(sub)
        assert new_num == 4
        assert old_num == 3

        project.make_folders(sub, ["04", "0005"])
        new_num, old_num = project.get_next_ses_number(sub)
        assert new_num == 6
        assert old_num == 5

    def test_invalid_sub_and_ses_name(self, project):
        with pytest.raises(BaseException) as e:
            project.make_folders("sub_100")

        assert "Invalid character in subject number: sub-sub_100" in str(
            e.value
        )

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001", "ses_100")

        assert "Invalid character in subject number: ses-ses_100" in str(
            e.value
        )

    # ----------------------------------------------------------------------------------
    # Test Helpers
    # ----------------------------------------------------------------------------------

    def get_formatted_date_and_time(self):
        date = str(datetime.datetime.now().date())
        date = date.replace("-", "")
        time_ = datetime.datetime.now().time().strftime("%Hh%Mm")
        return date, time_
