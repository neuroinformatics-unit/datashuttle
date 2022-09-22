import sys

sys.path.append("/Users/easyelectrophysiology/git-repos/project_manager_swc")
import warnings

import pytest

from manager import test_utils
from manager.manager import ProjectManager
from manager.utils import utils

TEST_PROJECT_NAME = "test_make_dirs"


class TestConfigs:
    """"""

    @pytest.fixture(scope="function")
    def project(test):
        """
        Fixture that creates an empty project. Ignore the warning
        that no configs are setup yet.
        """
        test_utils.delete_project_if_it_exists(TEST_PROJECT_NAME)

        warnings.filterwarnings("ignore")

        project = ProjectManager(TEST_PROJECT_NAME)
        default_configs = test_utils.get_test_config_arguments_dict(
            set_as_defaults=True
        )  # this is kind of wasteful but we need a fresh environment each time
        project.make_config_file(*default_configs.values())

        warnings.filterwarnings("default")

        project.update_config(
            "local_path", project.get_appdir_path() + "/base_dir"
        )  # put the test dir in the appdir path as it will be platform independent and not require tester to set paths

        yield project

    @pytest.mark.parametrize("prefix", ["sub-", "ses-"])
    @pytest.mark.parametrize(
        "input", [1, {"test": "one"}, 1.0, ["1", "2", ["three"]]]
    )
    def test_process_names_bad_input(self, input, prefix):
        """"""
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
        """"""
        exception_was_raised = False
        try:
            utils.process_names(["1", "2", "3", "3", "4"], prefix)
        except BaseException as e:
            assert (
                "Subject and session names but all be unqiue (i.e. there are no duplicates in list input)"
                == str(e)
            )

        assert exception_was_raised

    def test_process_names_prefix(self, project):
        """"""
        prefix = "test_sub-"
        processed_names = utils.process_names("1", prefix)
        assert processed_names[0] == "test_sub-1"

        processed_names = utils.process_names("test_sub-1", prefix)
        assert processed_names[0] == "test_sub-1"

        mixed_names = ["1", prefix + "four", "5", prefix + "6"]
        processed_names = utils.process_names(mixed_names, prefix)
        assert processed_names == [
            "test_sub-1",
            "test_sub-four",
            "test_sub-1",
            "test_sub-5",
            "test_sub-6",
        ]

    def test_generate_dirs_default_ses(self, project):
        breakpoint()

    def test_default_sub_prefix(self, project):
        pass

    def test_default_ses_prefix(self, project):
        pass

    def test_dirs_set_false(self, project):
        pass

    # think hard!
