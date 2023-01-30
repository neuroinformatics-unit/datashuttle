"""
# Still need to do more of this.
# 4) test all, in particular the removal of --ignore-existing. When the user transfers, it makes
#    sense to have a comment explicitly stating the nature of the transfer (or, at the end).

# https://stackoverflow.com/questions/18601828/python-block-network-connections-for-testing-purposes
# but these drop python access to internet NOT entire internet (at least some of them)

# PROJECT / SUB / SES LEVEL UNTRACKED FILES
# add keyword arguments a la #70

# Note: Use the -P/--progress flag to view real-time transfer statistics.

# new rclone args:
#   --progress
#   ignore-existing
#   verbosity

# dont forget to type everything!

# possible inputs
# ---------------

# sub_names: "all", "all_sub", "all_non_sub", [some sub names]

# ses_names: "all", "all_ses", "all_non_ses", [some ses_names]

# data_type: "all", "all_data_type", "all_ses_level_non_data_type", [some data type names]

# path table
# ---------------

# Path : full path to file
# is_dir : True if directory, False if file
# level : "project", "sub" or "ses" (i.e. it is in the top level folder (e.g. rawdata), subject levle, or session level.
# parent_sub : if ses file or other, name of the parent subject (otherwise None)
# parent_ses : if data type or other file, name of the parent session folder
# is_data_type : the data type if True, otherwise None

# DONT FORGET THIS IS SUPPOSE TO TEST OVER SSH
# ASK ALEX ABOUT SSH TO CEPH

# fmt: off

# this would work for data_type and all other files. But didn't work well for testing, so just use the files.
# TODO: fix naming

"""

import os
from pathlib import Path

import pandas as pd
import pytest
import test_utils


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

        test_project_name = "test_file_conflicts"
        project, cwd = test_utils.setup_project_fixture(
            tmp_path, test_project_name
        )

        yield project
        test_utils.teardown_project(cwd, project)

    def write_file(self, path_, contents, append=False):
        key = "a" if append else "w"
        with open(path_, key) as file:
            file.write(contents)

    def read_file(self, path_):
        with open(path_, "r") as file:
            contents = file.readlines()
        return contents

    @pytest.mark.skip
    @pytest.mark.parametrize("overwrite_old_files_on_transfer", [True, False])
    def test_rclone_overwrite_modified_file(
        self, project, overwrite_old_files_on_transfer
    ):
        """
        Test how rclone deals with existing files. In datashuttle
        if project.cfg["overwrite_old_files_on_transfer"] is on,
        files will be replaced with newer versions. Alternatively,
        if this is off, files will never be overwritten even if
        the version in source is newer than target.
        """
        path_to_test_file = (
            Path("rawdata") / "sub-001" / "histology" / "test_file.txt"
        )

        project.make_sub_dir("sub-001")
        local_test_file_path = project.cfg["local_path"] / path_to_test_file
        remote_test_file_path = project.cfg["remote_path"] / path_to_test_file

        # Write a local file and transfer
        self.write_file(local_test_file_path, contents="first edit")

        time_written = os.path.getatime(local_test_file_path)

        if overwrite_old_files_on_transfer:
            project.update_config("overwrite_old_files_on_transfer", True)

        project.upload_all()

        # Update the file and transfer and transfer again
        self.write_file(
            local_test_file_path, contents=" second edit", append=True
        )

        assert time_written < os.path.getatime(local_test_file_path)

        project.upload_all()

        remote_contents = self.read_file(remote_test_file_path)

        if overwrite_old_files_on_transfer:
            assert remote_contents == ["first edit second edit"]
        else:
            assert remote_contents == ["first edit"]

    @pytest.mark.parametrize(
        "sub_names",
        [
            ["all"],
            ["all_sub"],
            ["all_non_sub"],
            ["sub-001"],
            ["sub-003_date-20231901"],
            ["sub-002", "all_non_sub"],
        ],
    )
    @pytest.mark.parametrize(
        "ses_names", [["all"], ["all_ses"], ["all_non_ses"], ["ses_002"]]
    )
    @pytest.mark.parametrize(
        "data_type",
        [
            ["all"],
            ["all_ses_level_non_data_type"],
            ["behav"],
            ["ephys"],
            ["histology"],
            ["funcimg"],
            ["histology", "behav", "all_ses_level_non_data_type"],
        ],
    )
    def test_all_data_transfer_options(
        self, project, sub_names, ses_names, data_type
    ):
        """ """
        base_dir = project.cfg["local_path"]

        columns = [
            "base_dir",
            "path",
            "is_non_sub",
            "is_non_ses",
            "is_ses_level_non_data_type",
            "parent_sub",
            "parent_ses",
            "parent_data_type",
        ]

        # base_dir                                  path                                                                 #is_non_sub    # is_non_ses   is_ses_level_non_data_type       parent_sub                 parent_ses                 parent_data_type
        data = [
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "ses-001"
                / "sub-001_ses-001_data-file",
                False,
                False,
                True,
                "sub-001",
                "ses-001",
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "ses-002_random-key"
                / "random-key-file.mp4",
                False,
                False,
                True,
                "sub-001",
                "ses-002_random-key",
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "ses-003_date-20231901"
                / "behav"
                / "behav.csv",
                False,
                False,
                False,
                "sub-001",
                "ses-003_date-20231901",
                "behav",
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "ses-003_date-20231901"
                / "ephys"
                / "ephys.bin",
                False,
                False,
                False,
                "sub-001",
                "ses-003_date-20231901",
                "ephys",
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "ses-003_date-20231901"
                / "non_data"
                / "non_data.mp4",
                False,
                False,
                True,
                "sub-001",
                "ses-003_date-20231901",
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "ses-003_date-20231901"
                / "nondata_type_level_file.csv",
                False,
                False,
                True,
                "sub-001",
                "ses-003_date-20231901",
                None,
            ],
            [
                base_dir,
                Path("rawdata") / "sub-001" / "random-ses_level_file.mp4",
                False,
                True,
                False,
                "sub-001",
                None,
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-001"
                / "histology"
                / "sub-001_histology.file",
                False,
                False,
                False,
                "sub-001",
                None,
                "histology",
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-002_random-value"
                / "sub-002_random-value.file",
                False,
                True,
                False,
                "sub-002_random-value",
                None,
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-002_random-value"
                / "ses-001"
                / "non_data_type_level_dir"
                / "file.csv",
                False,
                False,
                True,
                "sub-002_random-value",
                "ses-001",
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-003_date-20231901"
                / "ses-001"
                / "funcimg"
                / ".myfile.xlsx",
                False,
                False,
                False,
                "sub-003_date-20231901",
                "ses-001",
                "funcimg",
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-003_date-20231901"
                / "ses-003_date-20231901"
                / "nondata_type_level_file.csv",
                False,
                False,
                True,
                "sub-003_date-20231901",
                "ses-003_date-20231901",
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-003_date-20231901"
                / "ses-003_date-20231901"
                / "funcimg"
                / "funcimg.nii",
                False,
                False,
                False,
                "sub-003_date-20231901",
                "ses-003_date-20231901",
                "funcimg",
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-003_date-20231901"
                / "seslevel_non-prefix_dir"
                / "nonlevel.mat",
                False,
                True,
                False,
                "sub-003_date-20231901",
                "seslevel_non-prefix_dir",
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-003_date-20231901"
                / "sub-ses-level_file.txt",
                False,
                True,
                False,
                "sub-003_date-20231901",
                None,
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sub-003_date-20231901"
                / "histology"
                / ".histology.file",
                False,
                False,
                False,
                "sub-003_date-20231901",
                None,
                "histology",
            ],
            [
                base_dir,
                Path("rawdata") / "project_level_file.txt",
                True,
                False,
                False,
                None,
                None,
                None,
            ],
            [
                base_dir,
                Path("rawdata")
                / "sublevel_non_sub-prefix_dir"
                / "ses_non_dir.file",
                True,
                False,
                False,
                None,
                None,
                None,
            ],
        ]

        # fmt: on  # todo: Move to dedicated file

        pathtable = pd.DataFrame(data, columns=columns)

        for i in range(pathtable.shape[0]):
            filepath = pathtable["base_dir"][i] / pathtable["path"][i]
            filepath.parents[0].mkdir(parents=True, exist_ok=True)
            self.write_file(filepath, contents="test_entry")

        project.upload_data(sub_names, ses_names, data_type)

        if sub_names == ["all"]:  # TODO: fix
            sub_names = list(
                set(pathtable.query("parent_sub != False")["parent_sub"])
            ) + [
                "all_non_sub"
            ]  # can fix this, one function one name,
        elif sub_names == ["all_sub"]:
            sub_names = list(
                set(pathtable.query("parent_sub != False")["parent_sub"])
            )

        if ses_names == ["all"]:
            ses_names = list(
                set(pathtable.query("parent_ses != False")["parent_ses"])
            ) + ["all_non_ses"]
        elif ses_names == ["all_ses"]:
            ses_names = list(
                set(pathtable.query("parent_ses != False")["parent_ses"])
            )

        if data_type == ["all"]:
            data_type = list(
                set(
                    pathtable.query("parent_data_type != False")[
                        "parent_data_type"
                    ]
                )
            ) + ["all_ses_level_non_data_type"]
        elif data_type == ["all_data_type"]:
            data_type = list(
                set(
                    pathtable.query("parent_data_type != False")[
                        "parent_data_type"
                    ]
                )
            )

        extra_arguments = []
        sub_ses_dtype_arguments = []

        for sub in sub_names:

            if sub == "all_non_sub":
                extra_arguments += ["is_non_sub == True"]

            else:
                if "histology" in data_type:
                    sub_ses_dtype_arguments += [
                        f"(parent_sub == '{sub}' & (parent_data_type == 'histology' | parent_data_type == 'histology'))"
                    ]

                for ses in ses_names:

                    if ses == "all_non_ses":
                        extra_arguments += [
                            f"(parent_sub == '{sub}' & is_non_ses == True)"
                        ]

                    else:

                        for dtype in data_type:
                            if dtype == "all_ses_level_non_data_type":
                                extra_arguments += [
                                    f"(parent_sub == '{sub}' & parent_ses == '{ses}' & is_ses_level_non_data_type == True)"
                                ]

                            else:
                                sub_ses_dtype_arguments += [
                                    f"(parent_sub == '{sub}' & parent_ses == '{ses}' & (parent_data_type == '{dtype}' | parent_data_type == '{dtype}'))"
                                ]

        if any(sub_ses_dtype_arguments):
            try:
                data_type_folders = pathtable.query(
                    " | ".join(sub_ses_dtype_arguments)
                )
            except:
                breakpoint()
        else:
            data_type_folders = pd.DataFrame()

        if any(extra_arguments):
            extra_folders = pathtable.query(" | ".join(extra_arguments))
        else:
            extra_folders = pd.DataFrame()

        result = pd.concat([data_type_folders, extra_folders])

        result = result.drop_duplicates(subset="path")

        get_every_path = project.cfg["remote_path"].glob("**/*")
        get_every_path = [
            Path(path_).as_posix()
            for path_ in get_every_path
            if path_.is_file()
        ]

        test_move_paths = result.base_dir / result.path
        test_move_paths = [
            path_.as_posix().replace("local", "remote")
            for path_ in test_move_paths
        ]  # this will be slow

        assert sorted(get_every_path) == sorted(test_move_paths)
