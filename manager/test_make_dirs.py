import os.path
import sys

sys.path.append("/Users/easyelectrophysiology/git-repos/project_manager_swc")
import datetime
import glob
import re
from os.path import join

import pytest

from manager import test_utils
from manager.utils import utils

TEST_PROJECT_NAME = "test_make_dirs"


def get_default_directory_used():  # TODO: need to find a way to know to update this when new ones added
    return {
        "ephys": True,
        "ephys_behav": True,
        "ephys_behav_camera": True,
        "behav": True,
        "behav_camera": True,
        "imaging": True,
        "histology": True,
    }


class TestMakeDirs:
    """"""

    @pytest.fixture(scope="function")
    def project(test):
        """
        Create a project with default configs loaded. This makes a fresh project
        for each function, saved in the appdir path for platform independent and to
        avoid path setup on new machine.

        Ensure change dir at end of session otherwise it is not possible
        to delete project.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        project = test_utils.setup_project_default_configs(TEST_PROJECT_NAME)

        cwd = os.getcwd()
        yield project
        os.chdir(cwd)

    # ----------------------------------------------------------------------------------------------------------
    # Tests
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("prefix", ["sub-", "ses-"])
    @pytest.mark.parametrize(
        "input", [1, {"test": "one"}, 1.0, ["1", "2", ["three"]]]
    )
    def test_process_names_bad_input(self, input, prefix):
        """
        Test that names passed in incorrect type (not str, list) raise appropriate error.
        """
        exception_was_raised = False
        try:
            utils.process_names(input, prefix)
        except BaseException as e:
            assert (
                "Ensure subject and session names are list of strings, or string"
                == str(e)
            )
            exception_was_raised = True

        assert exception_was_raised

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_process_names_duplicate_ele(self, prefix):
        """
        Test that appropriate error is raised when duplicate name
        is passed to process_names().
        """
        exception_was_raised = False
        try:
            utils.process_names(["1", "2", "3", "3", "4"], prefix)
        except BaseException as e:
            assert (
                "Subject and session names but all be unqiue (i.e. there are no duplicates in list input)"
                == str(e)
            )
        exception_was_raised = True

        assert exception_was_raised

    def test_process_names_prefix(self, project):
        """
        Check that process_names correctly prefixes input
        with default sub- or ses- prefix.
        """
        prefix = "test_sub-"

        # check name is prefixed
        processed_names = utils.process_names("1", prefix)
        assert processed_names[0] == "test_sub-1"

        # check existing prefix is not duplicated
        processed_names = utils.process_names("test_sub-1", prefix)
        assert processed_names[0] == "test_sub-1"

        # test mixed list of prefix and unprefixed are prefixed correctly.
        mixed_names = ["1", prefix + "four", "5", prefix + "6"]
        processed_names = utils.process_names(mixed_names, prefix)
        assert processed_names == [
            "test_sub-1",
            "test_sub-four",
            "test_sub-5",
            "test_sub-6",
        ]

    def test_generate_dirs_default_ses(self, project):
        """
        Make a subject directories with full tree. Don't specify
        session name (it will default to ses-001).

        Check that the directory tree is created correctly. Pass
        a dict that indicates if each subdir is used (to avoid
        circular testing from the project itself).
        """
        subs = ["1_1", "sub-two-2", "3_3-3=3"]

        project.make_sub_dir("all", subs)

        self.check_directory_tree_is_made(
            project,
            base_dir=project.get_local_path(),
            subs=["sub-1_1", "sub-two-2", "sub-3_3-3=3"],
            sessions=["ses-001"],
            directory_used=get_default_directory_used(),
        )

    def test_explicitly_session_list(self, project):
        """
        Perform an alternative test where the output is tested explicitly.
        This is some redundancy to ensure tests are working correctly and
        make explicit the expected directory tree.

        Note for new directories, this will have to be manually updated.
        This is highlighted in an assert in check_and_cd_dir()
        """
        subs = ["sub-001", "sub-002"]
        sessions = ["ses-001", "="]
        project.make_sub_dir("all", subs, sessions)
        base_dir = project.get_local_path()

        for sub in subs:
            for ses in ["ses-001", "ses-="]:
                self.check_and_cd_dir(
                    join(base_dir, "behav", sub, ses, "camera")
                )
                self.check_and_cd_dir(
                    join(base_dir, "ephys", sub, ses, "behav", "camera")
                )
                self.check_and_cd_dir(join(base_dir, "histology", sub, ses))
                self.check_and_cd_dir(join(base_dir, "imaging", sub, ses))

    @pytest.mark.parametrize("dir_key", get_default_directory_used().keys())
    def test_turn_off_specific_directory_used(self, project, dir_key):
        """
        Whether or not a directory is made is held in the .used key of the
        Directory class (stored in project._ses_dirs).
        """

        # Overwrite configs to make specified directory not used.
        project.update_config("use_" + dir_key, False)
        directory_used = get_default_directory_used()
        directory_used[dir_key] = False

        # Make dir tree
        subs = ["sub-001", "sub-002"]
        sessions = ["ses-001", "ses-002"]
        project.make_sub_dir("all", subs, sessions)

        # Check dir tree is not made but all others are
        self.check_directory_tree_is_made(
            project,
            base_dir=project.get_local_path(),
            subs=subs,
            sessions=sessions,
            directory_used=directory_used,
        )

    def test_custom_directory_names(self, project):
        """
        Change directory names to custom (non-default) and ensure they are made
        correctly.
        """
        # Change directory names to custom names
        project._ses_dirs["ephys"].name = "change_ephys"
        project._ses_dirs["ephys"].subdirs[
            "ephys_behav"
        ].name = "change_ephys_behav"
        project._ses_dirs["ephys"].subdirs["ephys_behav"].subdirs[
            "ephys_behav_camera"
        ].name = "change_ephys_behav_camera"

        project._ses_dirs["behav"].name = "change_behav"
        project._ses_dirs["behav"].subdirs[
            "behav_camera"
        ].name = "change_behav_camera"

        project._ses_dirs["histology"].name = "change_histology"
        project._ses_dirs["imaging"].name = "change_imaging"

        # Make the directories
        sub = "sub-001"
        ses = "ses-001"
        project.make_sub_dir("all", sub, ses)

        # Check the directories were not made / made.
        base_dir = project.get_local_path()
        self.check_and_cd_dir(
            join(
                base_dir,
                "change_ephys",
                sub,
                ses,
                "change_ephys_behav",
                "change_ephys_behav_camera",
            )
        )
        self.check_and_cd_dir(
            join(base_dir, "change_behav", sub, ses, "change_behav_camera")
        )
        self.check_and_cd_dir(join(base_dir, "change_histology", sub, ses))
        self.check_and_cd_dir(join(base_dir, "change_imaging", sub, ses))

    def test_make_sub_dir_no_tree(self, project):
        """
        Make sub directory only, check it is made and no lower level dirs exist
        """
        project.make_sub_dir("ephys", "001", make_ses_tree=False)
        sub_path = join(project.get_local_path(), "ephys", "sub-001")
        self.check_and_cd_dir(sub_path)
        assert glob.glob(join(sub_path, "*")) == []

    def test_make_sub_dir_with_ses_no_tree(self, project):
        """
        Make ses directory (in a sub dir) only, and check no lower level dirs exist
        """
        project.make_sub_dir("ephys", "001", "001", make_ses_tree=False)
        ses_path = join(
            project.get_local_path(), "ephys", "sub-001", "ses-001"
        )
        self.check_and_cd_dir(ses_path)
        assert glob.glob(join(ses_path, "*")) == []

    def test_make_empty_ses_dir(self, project):
        """
        Make an empty sub directory, checking no lower level dirs exist
        """
        project.make_empty_ses_dir("ephys", "001", "001")
        ses_path = join(
            project.get_local_path(), "ephys", "sub-001", "ses-001"
        )
        self.check_and_cd_dir(ses_path)
        assert glob.glob(join(ses_path, "*")) == []

    def test_default_sub_prefix(self, project):
        """
        Change the default subject prefix and check dirs are created correctly.
        Note this is very similar to test_default_ses_prefix(), but trying to combine
        made the tests very difficult to follow.
        """
        project.update_config("sub_prefix", "edited_sub_prefix_")
        project.make_sub_dir(
            "ephys",
            ["sub-001", "001", "edited_sub_prefix_1"],
            make_ses_tree=False,
        )

        base_path = join(project.get_local_path(), "ephys")
        self.check_and_cd_dir(join(base_path, "edited_sub_prefix_sub-001"))
        self.check_and_cd_dir(join(base_path, "edited_sub_prefix_001"))
        self.check_and_cd_dir(join(base_path, "edited_sub_prefix_1"))

    def test_default_ses_prefix(self, project):
        """
        Change the default session prefix and check dirs are created correctly.
        """
        project.update_config("ses_prefix", "edited_ses_prefix_")
        sub = "sub-001"

        project.make_empty_ses_dir(
            "ephys", sub, ["ses-001", "001", "edited_ses_prefix_1"]
        )

        base_path = join(project.get_local_path(), "ephys")

        self.check_and_cd_dir(
            join(base_path, sub, "edited_ses_prefix_ses-001")
        )
        self.check_and_cd_dir(join(base_path, sub, "edited_ses_prefix_001"))
        self.check_and_cd_dir(join(base_path, sub, "edited_ses_prefix_1"))

    @pytest.mark.parametrize(
        "file_info",
        [
            ["all"],
            ["ephys", "behav"],
            ["ephys", "behav", "histology"],
            ["ephys", "behav", "histology", "imaging"],
            ["imaging", "ephys"],
        ],
    )
    def test_experimental_data_subsection(self, project, file_info):
        """
        Check that combinations of experiment_types passed to make file dir
        make the correct combination of epxeriment types.

        Note this will fail when new top level dirs are added, and should be
        updated.
        """
        project.make_sub_dir(file_info, "sub-001", make_ses_tree=False)

        file_paths = glob.glob(join(project.get_local_path(), "*"))
        file_names = [os.path.basename(path_) for path_ in file_paths]

        if file_info == ["all"]:
            assert file_names == sorted(
                ["ephys", "behav", "histology", "imaging"]
            )
        else:
            assert file_names == sorted(file_info)

    def test_date_flags_in_session(self, project):
        """
        Check that @DATE is converted into current date in generated directory names
        """
        date, time_ = self.get_formatted_date_and_time()

        project.make_sub_dir(
            "ephys", ["sub-001", "sub-002"], ["ses-001-@DATE", "002-@DATE"]
        )

        ses_paths = glob.glob(
            join(project.get_local_path(), "**", "ses-*"), recursive=True
        )
        ses_names = [os.path.basename(path_) for path_ in ses_paths]

        assert all([date in name for name in ses_names])
        assert all(["@DATE" not in name for name in ses_names])

    def test_datetime_flag_in_session(self, project):
        """
        Check that @DATETIME is converted to datetime in generated directory names
        """
        date, time_ = self.get_formatted_date_and_time()

        project.make_sub_dir(
            "ephys",
            ["sub-001", "sub-002"],
            ["ses-001-@DATETIME", "002-@DATETIME"],
        )

        ses_paths = glob.glob(
            join(project.get_local_path(), "**", "ses-*"), recursive=True
        )
        ses_names = [os.path.basename(path_) for path_ in ses_paths]

        # Convert the minutes to regexp as could change during test runtime
        regexp_time = time_[:-3] + r"\d\dm"
        datetime_regexp = f"{date}-{regexp_time}"

        assert all([re.search(datetime_regexp, name) for name in ses_names])
        assert all(["@DATETIME" not in name for name in ses_names])

    # ----------------------------------------------------------------------------------------------------------
    # Test Helpers
    # ----------------------------------------------------------------------------------------------------------

    def check_directory_tree_is_made(
        self, project, base_dir, subs, sessions, directory_used
    ):
        """
        Automated test that directories are made based on the structure specified on project itself.

        Cycle through all experiment type (defined in project._ses_dirs()), sub, sessions
        and check that the expected file exists. For subdirs, recursively check all exist.

        Directories in which directory_used[key] (where key is the cannoincal dict
        key in project._ses_dirs()) is not used are expected not to be made, and this is checked.

        The directory_used variable must be passed so we dont rely on project settings itself,
        as this doesn't explicitly test this.
        """
        for key, directory in project._ses_dirs.items():

            assert key in directory_used.keys(), (
                "Key not found in directory_used. "
                "Update directory used and hard-coded tests: test_custom_directory_names(), test_explicitly_session_list()"
            )

            if self.check_directory_is_used(
                base_dir, directory, directory_used, key
            ):
                self.check_and_cd_dir(join(base_dir, directory.name))

                for sub in subs:
                    self.check_and_cd_dir(join(base_dir, directory.name, sub))

                    for ses in sessions:
                        path_to_folder = join(
                            base_dir, directory.name, sub, ses
                        )
                        self.check_and_cd_dir(path_to_folder)

                        self.recursive_check_subfolder_exists(
                            path_to_folder, directory, directory_used
                        )

    def recursive_check_subfolder_exists(
        self, path_to_dir, upper_dir, directory_used
    ):
        """
        Check each subdir in the subdirs field on the Directory class are
        made, and that directory_used is as expected.
        """
        if upper_dir.subdirs:
            for key, subdir in upper_dir.subdirs.items():

                if self.check_directory_is_used(
                    path_to_dir, subdir, directory_used, key
                ):
                    new_path_to_dir = join(path_to_dir, subdir.name)

                    self.check_and_cd_dir(new_path_to_dir)
                    self.recursive_check_subfolder_exists(
                        new_path_to_dir, subdir, directory_used
                    )

    def check_directory_is_used(
        self, base_dir, directory, directory_used, key
    ):
        """
        Test whether the .used flag on the Directory class matched the expected
        state (provided in directory_used dict). If directory is not used, check
        it does not exist.

        Use the pytest -s flag to print all tested paths
        """
        assert directory.used == directory_used[key]

        is_used = directory.used

        if not is_used:
            print(
                "Path was correctly not made: "
                + join(base_dir, directory.name)
            )
            assert not os.path.isdir(join(base_dir, directory.name))

        return is_used

    def check_and_cd_dir(self, path_):
        """
        Check a directory exists and CD to it if it does.

        Use the pytest -s flag to print all tested paths
        """
        assert os.path.isdir(path_)
        os.chdir(path_)
        print(f"checked: {path_}")  # -s flag

    def get_formatted_date_and_time(self):
        date = str(datetime.datetime.now().date())
        time_ = datetime.datetime.now().time().strftime("%Hh%Mm")
        return date, time_
