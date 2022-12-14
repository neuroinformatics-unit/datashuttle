import datetime
import os.path
import re
from os.path import join

import pytest
import test_utils

from datashuttle.utils_mod import utils


class TestMakeDirs:
    """"""

    @pytest.fixture(scope="function")
    def project(test, tmp_path):
        """
        Create a project with default configs loaded.
        This makes a fresh project for each function,
        saved in the appdir path for platform independent
        and to avoid path setup on new machine.

        Ensure change dir at end of session otherwise
        it is not possible to delete project.
        """
        tmp_path = tmp_path / "test with space"

        test_project_name = "test_make_dirs"

        project = test_utils.setup_project_default_configs(
            test_project_name, local_path=tmp_path / test_project_name
        )

        cwd = os.getcwd()
        yield project
        test_utils.teardown_project(cwd, project)

    # ----------------------------------------------------------------------------------------------------------
    # Tests
    # ----------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("prefix", ["sub-", "ses-"])
    @pytest.mark.parametrize(
        "input", [1, {"test": "one"}, 1.0, ["1", "2", ["three"]]]
    )
    def test_format_names_bad_input(self, input, prefix):
        """
        Test that names passed in incorrect type
        (not str, list) raise appropriate error.
        """
        with pytest.raises(BaseException) as e:
            utils.format_names(input, prefix)

        assert (
            "Ensure subject and session names are "
            "list of strings, or string" == str(e.value)
        )

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_format_names_duplicate_ele(self, prefix):
        """
        Test that appropriate error is raised when duplicate name
        is passed to format_names().
        """
        with pytest.raises(BaseException) as e:
            utils.format_names(["1", "2", "3", "3", "4"], prefix)

        assert (
            "Subject and session names but all be unique "
            "(i.e. there are no duplicates in list input)" == str(e.value)
        )

    def test_format_names_prefix(self):
        """
        Check that format_names correctly prefixes input
        with default sub- or ses- prefix.
        """
        prefix = "test_sub-"

        # check name is prefixed
        processed_names = utils.format_names("1", prefix)
        assert processed_names[0] == "test_sub-1"

        # check existing prefix is not duplicated
        processed_names = utils.format_names("test_sub-1", prefix)
        assert processed_names[0] == "test_sub-1"

        # test mixed list of prefix and unprefixed are prefixed correctly.
        mixed_names = ["1", prefix + "four", "5", prefix + "6"]
        processed_names = utils.format_names(mixed_names, prefix)
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

        project.make_sub_dir(subs)

        test_utils.check_directory_tree_is_correct(
            project,
            base_dir=test_utils.get_rawdata_path(project),
            subs=["sub-1_1", "sub-two-2", "sub-3_3-3=3"],
            sessions=["ses-001"],
            directory_used=test_utils.get_default_directory_used(),
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
        project.make_sub_dir(subs, sessions)
        base_dir = test_utils.get_rawdata_path(project)

        for sub in subs:
            for ses in ["ses-001", "ses-="]:
                test_utils.check_and_cd_dir(join(base_dir, sub, ses, "ephys"))
                test_utils.check_and_cd_dir(
                    join(
                        base_dir,
                        sub,
                        ses,
                        "behav",
                    )
                )
                test_utils.check_and_cd_dir(
                    join(base_dir, sub, ses, "funcimg")
                )
                test_utils.check_and_cd_dir(join(base_dir, sub, "histology"))

    @pytest.mark.parametrize(
        "dir_key", test_utils.get_default_directory_used().keys()
    )
    def test_turn_off_specific_directory_used(self, project, dir_key):
        """
        Whether or not a directory is made is held in the .used key of the
        Directory class (stored in project._data_type_dirs).
        """

        # Overwrite configs to make specified directory not used.
        project.update_config("use_" + dir_key, False)
        directory_used = test_utils.get_default_directory_used()
        directory_used[dir_key] = False

        # Make dir tree
        subs = ["sub-001", "sub-002"]
        sessions = ["ses-001", "ses-002"]
        project.make_sub_dir(subs, sessions)

        # Check dir tree is not made but all others are
        test_utils.check_directory_tree_is_correct(
            project,
            base_dir=test_utils.get_rawdata_path(project),
            subs=subs,
            sessions=sessions,
            directory_used=directory_used,
        )

    def test_custom_directory_names(self, project):
        """
        Change directory names to custom (non-default) and
        ensure they are made correctly.
        """
        # Change directory names to custom names
        project._data_type_dirs["ephys"].name = "change_ephys"
        project._data_type_dirs["behav"].name = "change_behav"
        project._data_type_dirs["histology"].name = "change_histology"
        project._data_type_dirs["funcimg"].name = "change_funcimg"

        # Make the directories
        sub = "sub-001"
        ses = "ses-001"
        project.make_sub_dir(sub, ses)

        # Check the directories were not made / made.
        base_dir = test_utils.get_rawdata_path(project)
        test_utils.check_and_cd_dir(
            join(
                base_dir,
                sub,
                ses,
                "change_ephys",
            )
        )
        test_utils.check_and_cd_dir(join(base_dir, sub, ses, "change_behav"))
        test_utils.check_and_cd_dir(join(base_dir, sub, ses, "change_funcimg"))

        test_utils.check_and_cd_dir(join(base_dir, sub, "change_histology"))

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
    def test_dataal_data_subsection(self, project, files_to_test):
        """
        Check that combinations of data_types passed to make file dir
        make the correct combination of epxeriment types.

        Note this will fail when new top level dirs are added, and should be
        updated.
        """
        sub = "sub-001"
        ses = "ses-001"
        project.make_sub_dir(sub, ses, files_to_test)

        base_dir = test_utils.get_rawdata_path(project)

        # Check at the subject level
        sub_file_names = test_utils.glob_basenames(
            join(base_dir, sub, "*"),
            exclude=ses,
        )
        if "histology" in files_to_test:
            assert "histology" in sub_file_names
            files_to_test.remove("histology")

        # Check at the session level
        ses_file_names = test_utils.glob_basenames(
            join(base_dir, sub, ses, "*"),
            exclude=ses,
        )

        if files_to_test == ["all"]:
            assert ses_file_names == sorted(["ephys", "behav", "funcimg"])
        else:
            assert ses_file_names == sorted(files_to_test)

    def test_date_flags_in_session(self, project):
        """
        Check that @DATE@ is converted into current date
        in generated directory names
        """
        date, time_ = self.get_formatted_date_and_time()

        project.make_sub_dir(
            "ephys", ["sub-001", "sub-002"], ["ses-001-@DATE@", "002-@DATE@"]
        )

        ses_names = test_utils.glob_basenames(
            join(test_utils.get_rawdata_path(project), "**", "ses-*"),
            recursive=True,
        )

        assert all([date in name for name in ses_names])
        assert all(["@DATE@" not in name for name in ses_names])

    def test_datetime_flag_in_session(self, project):
        """
        Check that @DATETIME@ is converted to datetime
        in generated directory names
        """
        date, time_ = self.get_formatted_date_and_time()

        project.make_sub_dir(
            "ephys",
            ["sub-001", "sub-002"],
            ["ses-001-@DATETIME@", "002-@DATETIME@"],
        )

        ses_names = test_utils.glob_basenames(
            join(test_utils.get_rawdata_path(project), "**", "ses-*"),
            recursive=True,
        )

        # Convert the minutes to regexp as could change during test runtime
        regexp_time = time_[:-3] + r"\d\dm"
        datetime_regexp = f"{date}-{regexp_time}"

        assert all([re.search(datetime_regexp, name) for name in ses_names])
        assert all(["@DATETIME@" not in name for name in ses_names])

    # ----------------------------------------------------------------------------------------------------------
    # Test Helpers
    # ----------------------------------------------------------------------------------------------------------

    def get_formatted_date_and_time(self):
        date = str(datetime.datetime.now().date())
        date = date.replace("-", "")
        time_ = datetime.datetime.now().time().strftime("%Hh%Mm")
        return date, time_
