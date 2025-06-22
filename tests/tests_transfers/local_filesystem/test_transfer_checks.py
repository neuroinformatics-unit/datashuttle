import os
import shutil
from pathlib import Path

import pytest

from datashuttle.utils.rclone import get_local_and_central_file_differences

from ... import test_utils
from ...base import BaseTest


class TestTransferChecks(BaseTest):
    @pytest.mark.parametrize(
        "top_level_folders",
        [["rawdata", "derivatives"], ["rawdata"], ["derivatives"]],
    )
    def test_rclone_check(self, project, top_level_folders):
        """Test rclone.get_local_and_central_file_differences(). This function
        returns a dictionary where values are list of paths and keys
        separate based on differences between local and central projects.

        A file is either in local only, in central only, found in
        both and the same or found in both and different. RClone does
        not currently return why the different files are different, just
        that they are different (see question):
        https://forum.rclone.org/t/rclone-check-find-which-file-is-newer-if-there-is-a-difference/42853

        This test first builds a project in which files are found in
        all of the above cases. It then runs
        `get_local_and_central_file_differences()` and checks the output is
        as expected.
        """
        (local := project.cfg["local_path"]).mkdir(parents=True, exist_ok=True)
        (central := project.cfg["central_path"]).mkdir(
            parents=True, exist_ok=True
        )

        # Build the project according to the above spec
        folder_structure = []
        for top_level in top_level_folders:
            folder_structure.extend(self.get_folder_structure(top_level))

        for folder_info in folder_structure:
            path_, type_ = folder_info

            if type_ == "local_only":
                test_utils.write_file(local / path_)

            elif type_ == "central_only":
                test_utils.write_file(central / path_)

            elif type_ == "same":
                test_utils.write_file(local / path_)
                os.makedirs(central / Path(path_).parent, exist_ok=True)
                shutil.copy(local / path_, central / path_)

            else:
                if type_ == "newer_in_local":
                    test_utils.write_file(local / path_)
                    os.makedirs(central / Path(path_).parent, exist_ok=True)
                    shutil.copy(local / path_, central / path_)
                    test_utils.write_file(
                        local / path_, "new text", append=True
                    )

                elif type_ == "newer_in_central":
                    test_utils.write_file(local / path_)
                    os.makedirs(central / Path(path_).parent, exist_ok=True)
                    shutil.copy(local / path_, central / path_)
                    test_utils.write_file(
                        central / path_, "new text", append=True
                    )

        results = get_local_and_central_file_differences(
            project.cfg,
            top_level_folders_to_check=(top_level_folders),
        )

        # Check the results are sorted into cases correctly.
        for folder_info in folder_structure:
            path_, type_ = folder_info

            if type_ in ["newer_in_local", "newer_in_central"]:
                type_ = "different"

            for results_type, results_paths in results.items():
                if results_type == type_:
                    assert path_ in results_paths
                else:
                    assert path_ not in results_paths

    def get_folder_structure(self, top_level_folder):
        # fmt: off
        folder_structure = [
            [f"{top_level_folder}/sub-001/ses-001/ephys/local_only_1.txt",          "local_only"],
            [f"{top_level_folder}/sub-001/ses-001/behav/same_2.txt",                "same"],
            [f"{top_level_folder}/sub-001/ses-002/anat/local_only_3.txt",           "local_only"],
            [f"{top_level_folder}/sub-001/ses-002/anat/central_only_4.txt",         "central_only"],
            [f"{top_level_folder}/sub-001/ses-003/ephys/newer_in_central_5.txt",    "newer_in_central"],
            [f"{top_level_folder}/sub-002/ses-002/anat/same_6.txt",                 "same"],
            [f"{top_level_folder}/sub-003/ses-003/behav/newer_in_central_7.txt",    "newer_in_central"],
            [f"{top_level_folder}/sub-003/ses-004/funcimg/newer_in_local_8.txt",    "newer_in_local"],
            [f"{top_level_folder}/sub-004/ses-005/behav/newer_in_local_9.txt",      "newer_in_local"],
            [f"{top_level_folder}/sub-005/ses-001/ephys/same_10.txt",               "same"],
            [f"{top_level_folder}/sub-005/ses-001/ephys/local_only_11.txt",         "local_only"],
            [f"{top_level_folder}/sub-005/ses-001/ephys/central_only_12.txt",       "central_only"],
        ]
        # fmt: on
        return folder_structure
