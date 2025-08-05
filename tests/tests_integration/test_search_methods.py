from pathlib import Path

import pytest

from .. import test_utils
from ..base import BaseTest

# -----------------------------------------------------------------------------
# Inconsistent sub or ses value lengths
# -----------------------------------------------------------------------------


class TestSubSesSearches(BaseTest):
    # TODO: return full path
    @pytest.mark.parametrize("return_full_path", [True, False])
    def test_local_vs_central_search_methods(
        self, project, monkeypatch, return_full_path
    ):
        """ """
        central_path = project.get_central_path()

        # fmt: off
        paths_to_make = []
        for i in range(1, 4):
            paths_to_make.append(Path(f"rawdata/sub-00{i}/ses-001/behav"))
            paths_to_make.append(Path(f"rawdata/sub-00{i}/ses-002_date-20250402/behav"))
            paths_to_make.append(Path(f"rawdata/sub-00{i}/ses-002_date-20250402/anat"))

        paths_to_make.append(Path("rawdata/sub-003_condition-test/ses-001_hello-world/ephys"))
        paths_to_make.append(Path("rawdata/sub-004_condition-test/ses-002_hello-world/funcimg"))

        for path_ in paths_to_make:
            (central_path / path_).mkdir(parents=True)
            test_utils.write_file(central_path / path_ / f"{path_.name}_file.md", contents="hello_world",)
            test_utils.write_file(central_path / path_.parent / f"{path_.name}.md", contents="hello_world",)
            test_utils.write_file(central_path / path_.parent.parent / f"{path_.parent.name}.md", contents="hello_world",)
            test_utils.write_file(central_path / path_.parent.parent.parent / f"{path_.parent.parent.name}.md", contents="hello_world",)
        # fmt: on

        from datashuttle.utils.folders import (
            search_central_via_connection,
            search_local_filesystem,
        )

        # -- monkeypatch cfg.get_rclone_config to return dummy config
        monkeypatch.setattr(
            project.cfg,
            "get_rclone_config_name",
            lambda connection_method: "local",
        )

        import subprocess

        subprocess.run(
            ["rclone", "config", "create", "local", "local", "nounc", "true"],
            shell=True,
        )

        for search_path, search_str in (
            (central_path / "rawdata", "*"),
            (central_path / "rawdata", "sub-*"),
            (central_path / "rawdata" / "sub-003_condition-test", "ses-*"),
            (central_path / "rawdata/sub-001/ses-002_date-20250402", "behav"),
            (
                central_path / "rawdata/sub-001/ses-002_date-20250402/behav",
                "behav_file.md",
            ),  # ses-002_date-20250402
            (
                central_path / "rawdata/sub-001/ses-002_date-20250402/behav",
                "*",
            ),
            (central_path / "rawdata/sub-002", "*"),
            (central_path / "rawdata/sub-002/ses-002_date-20250402", "*"),
            (central_path / "rawdata", "sub-003*"),
        ):
            central_method_folders, central_method_files = (
                search_central_via_connection(
                    project.cfg,
                    search_path,
                    search_str,
                    return_full_path=return_full_path,
                )
            )
            local_method_folders, local_method_files = search_local_filesystem(
                search_path, search_str, return_full_path=return_full_path
            )

            assert central_method_folders == local_method_folders, (
                f"Failed folders, search_str: {search_str}, search_path: {search_path}"
            )
            assert central_method_files == local_method_files, (
                f"Failed files, search_str: {search_str}, search_path: {search_path}"
            )
