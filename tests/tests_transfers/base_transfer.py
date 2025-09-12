""" """

import copy
import shutil
from pathlib import Path

import pandas as pd
import pytest

from datashuttle.utils import rclone

from .. import test_utils
from ..base import BaseTest
from .file_conflicts_pathtable import get_pathtable


class BaseTransfer(BaseTest):
    """
    Class holding fixtures and methods for testing the
    custom transfers with keys (e.g. all_non_sub).
    """

    @pytest.fixture(
        scope="class",
    )
    def pathtable_and_project(self, tmpdir_factory):
        """
        Create a new test project with a test project folder
        and file structure (see `get_pathtable()` for definition).
        """
        tmp_path = tmpdir_factory.mktemp("test")

        base_path = tmp_path / "test with space"
        test_project_name = "test_file_conflicts"

        project = test_utils.setup_project_fixture(
            base_path, test_project_name
        )

        pathtable = get_pathtable(project.cfg["local_path"])

        self.create_all_pathtable_files(pathtable)

        yield [pathtable, project]

        test_utils.teardown_project(project)

    def get_expected_transferred_paths(
        self, pathtable, sub_names, ses_names, datatype
    ):
        """
        Process the expected files that are transferred using the logic in
        `make_pathtable_search_filter()` to
        """
        parsed_sub_names = self.parse_arguments(pathtable, sub_names, "sub")
        parsed_ses_names = self.parse_arguments(pathtable, ses_names, "ses")
        parsed_datatype = self.parse_arguments(pathtable, datatype, "datatype")

        # Filter pathtable to get files that were expected to be transferred
        (
            sub_ses_dtype_arguments,
            extra_arguments,
        ) = self.make_pathtable_search_filter(
            parsed_sub_names, parsed_ses_names, parsed_datatype
        )

        datatype_folders = self.query_table(pathtable, sub_ses_dtype_arguments)
        extra_folders = self.query_table(pathtable, extra_arguments)

        expected_paths = pd.concat([datatype_folders, extra_folders])
        expected_paths = expected_paths.drop_duplicates(subset="path")

        expected_paths = self.remove_path_before_rawdata(expected_paths.path)

        return expected_paths

    def make_pathtable_search_filter(self, sub_names, ses_names, datatype):
        """
        Create a string of arguments to pass to pd.query() that will
        create the table of only transferred sub, ses and datatype.

        Two arguments must be created, one of all sub / ses / datatypes
        and the other of all non sub/ non ses / non datatype
        folders. These must be handled separately as they are
        mutually exclusive.
        """
        sub_ses_dtype_arguments = []
        extra_arguments = []

        for sub in sub_names:
            if sub == "all_non_sub":
                extra_arguments += ["is_non_sub == True"]
            else:
                for ses in ses_names:
                    if ses == "all_non_ses":
                        extra_arguments += [
                            f"(parent_sub == '{sub}' & is_non_ses == True)"
                        ]
                    else:
                        for dtype in datatype:
                            if dtype == "all_non_datatype":
                                extra_arguments += [
                                    f"(parent_sub == '{sub}' & parent_ses == '{ses}' "
                                    f"& is_ses_level_non_datatype == True)"
                                ]
                            else:
                                sub_ses_dtype_arguments += [
                                    f"(parent_sub == '{sub}' & parent_ses == '{ses}' "
                                    f"& parent_datatype == '{dtype}' )"
                                ]

        return sub_ses_dtype_arguments, extra_arguments

    def remove_path_before_rawdata(self, list_of_paths):
        """
        Remove the path to project files before the "rawdata" so
        they can be compared no matter where the project was stored
        (e.g. on a central server vs. local filesystem).
        """
        cut_paths = []
        for path_ in list_of_paths:
            parts = Path(path_).parts
            cut_paths.append(Path(*parts[parts.index("rawdata") :]))
        return cut_paths

    def query_table(self, pathtable, arguments):
        """
        Search the table for arguments, return empty
        if arguments empty
        """
        if any(arguments):
            folders = pathtable.query(" | ".join(arguments))
        else:
            folders = pd.DataFrame()
        return folders

    def parse_arguments(self, pathtable, list_of_names, field):
        """
        Replicate datashuttle name formatting by parsing
        "all" arguments and turning them into a list of all names,
        (subject or session), taken from the pathtable.
        """
        if list_of_names in [["all"], [f"all_{field}"]]:
            entries = pathtable.query(f"parent_{field} != False")[
                f"parent_{field}"
            ]
            entries = list(set(entries))
            if list_of_names == ["all"]:
                entries += [f"all_non_{field}"]
            list_of_names = entries
        return list_of_names

    def create_all_pathtable_files(self, pathtable):
        """
        Create the entire test project in the defined
        location (usually project's `local_path`).
        """
        for i in range(pathtable.shape[0]):
            filepath = pathtable["base_folder"][i] / pathtable["path"][i]
            filepath.parents[0].mkdir(parents=True, exist_ok=True)
            test_utils.write_file(filepath, contents="test_entry")

    def central_from_local(self, path_):
        return Path(str(copy.copy(path_)).replace("local", "central"))

    # -------------------------------------------------------------------------
    # Transfer
    # -------------------------------------------------------------------------

    def run_and_check_transfers(
        self,
        project,
        sub_names,
        ses_names,
        datatype,
        expected_transferred_paths,
    ):
        """Transfer the data and check the transferred files match the
        `expected_transferred_paths`.

        In test setup, the entire project is created in the `local_path` and
        is uploaded to `central_path`. So we only need to set up once for all
        tests, upload and download is to temporary folders and these temporary
        folders are cleaned at the end of each parameterization.
        """

        # Upload data from the setup local project to a temporary
        # central directory.
        true_central_path = project.cfg["central_path"]
        tmp_central_path = (
            project.cfg["central_path"] / "tmp" / project.project_name
        )
        self.remake_logging_path(project)

        project.update_config_file(central_path=tmp_central_path)

        project.upload_custom(
            "rawdata", sub_names, ses_names, datatype, init_log=False
        )

        # Search the paths that were transferred and tidy them up,
        # then check against the paths that were expected to be transferred.
        transferred_files = test_utils.recursive_search_central(project)
        paths_to_transferred_files = self.remove_path_before_rawdata(
            transferred_files
        )

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        ), f"Paths do not match. Failed project configs: {project.cfg}"

        # Now, move data from the central path where the project is
        # set up, to a temp local folder to test download.
        true_local_path = project.cfg["local_path"]
        tmp_local_path = (
            project.cfg["local_path"] / "tmp" / project.project_name
        )
        tmp_local_path.mkdir(exist_ok=True, parents=True)

        project.update_config_file(local_path=tmp_local_path)
        project.update_config_file(central_path=true_central_path)

        project.download_custom(
            "rawdata", sub_names, ses_names, datatype, init_log=False
        )

        # Find the transferred paths, tidy them up
        # and check expected paths were transferred.
        all_transferred = list((tmp_local_path / "rawdata").glob("**/*"))
        all_transferred = [
            path_ for path_ in all_transferred if path_.is_file()
        ]

        paths_to_transferred_files = self.remove_path_before_rawdata(
            all_transferred
        )

        assert sorted(paths_to_transferred_files) == sorted(
            expected_transferred_paths
        )

        # Clean up, removing the temp directories and
        # resetting the project paths.
        rclone.call_rclone(
            f"purge {project.cfg.get_rclone_config_name()}:{tmp_central_path.as_posix()} {rclone.get_config_arg(project.cfg)}"
        )

        shutil.rmtree(tmp_local_path)

        self.remake_logging_path(project)
        project.update_config_file(local_path=true_local_path)

    def remake_logging_path(self, project):
        """
        Need to do this to compensate for switching
        local_path location in the test environment.
        """
        project.get_logging_path().mkdir(parents=True, exist_ok=True)
