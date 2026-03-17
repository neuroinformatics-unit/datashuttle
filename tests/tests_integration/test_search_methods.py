import json
import subprocess
from pathlib import Path

import pytest

from datashuttle.utils.folders import (
    search_central_via_connection,
    search_local_filesystem,
)
from datashuttle.utils.rclone import call_rclone

from .. import test_utils
from ..base import BaseTest

# -----------------------------------------------------------------------------
# Inconsistent sub or ses value lengths
# -----------------------------------------------------------------------------


class TestSubSesSearches(BaseTest):
    @pytest.mark.parametrize("return_full_path", [True, False])
    def test_local_vs_central_search_methods(
        self, project, monkeypatch, return_full_path
    ):
        """
        Test the `search_local_filesystem` and `search_central_via_connection`
        functions. These functions should have the same outputs but `search_local_filesystem`
        is used for local filesystem for speed. Here we check the outputs of these
        functions match.

        These functions are individually tested in many places, primarily in
        transfer tests. Local filesystem transfer tests are very extensive,
        because they are quicker, while central connection tests are less
        thorough. We test the outputs of these two functions directly
        under a range of test cases to ensure they are matched under many conditions.

        """
        central_path = project.get_central_path()

        # Create a project of folders and files
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

        # search_central_via_connection will run the transfer
        # function but with additional checks for rclone password
        # through `run_function_that_requires_encrypted_rclone_config_access`.
        # Here we monkeypatch that to skip all of those checks.
        call_rclone(r"config create local local nounc true")

        from datashuttle.utils import rclone

        def mock_rclone_caller(_, func, optional=None):
            return func()

        monkeypatch.setattr(
            rclone,
            "run_function_that_requires_encrypted_rclone_config_access",
            mock_rclone_caller,
        )

        # Perform a range of checks across folders and files
        # and check the outputs of both approaches match.
        # fmt: off
        for search_path, search_str in (
            (central_path / "rawdata", "*"),
            (central_path / "rawdata", "sub-*"),
            (central_path / "rawdata" / "sub-003_condition-test", "ses-*"),
            (central_path / "rawdata/sub-001/ses-002_date-20250402", "behav"),
            (central_path / "rawdata/sub-001/ses-002_date-20250402/behav", "behav_file.md",),
            (central_path / "rawdata/sub-001/ses-002_date-20250402/behav", "*",),
            (central_path / "rawdata/sub-002", "*"),
            (central_path / "rawdata/sub-002/ses-002_date-20250402", "*"),
            (central_path / "rawdata", "sub-003*"),
        ):
        # fmt: on

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

    @pytest.mark.parametrize("return_full_path", [True, False])
    def test_search_central_none_search_path(
        self, project, monkeypatch, return_full_path
    ):
        """
        Test `search_central_via_connection` when `search_path=None`.

        When `search_path` is `None` (as is the case for Google Drive, where
        `cfg["central_path"]` can be `None`), the function should search from
        the root of the remote drive without error.

        Verify that:
        - the function handles ``search_path=None`` without raising
        - when ``return_full_path=True``, returned items are :class:`~pathlib.Path`
          objects relative to the remote root (e.g. ``Path("sub-001")``)
        - when ``return_full_path=False``, returned items are plain strings
        """
        from datashuttle.utils import rclone

        fake_entries = [
            {"Name": "sub-001", "IsDir": True},
            {"Name": "sub-002", "IsDir": True},
            {"Name": "rawdata.md", "IsDir": False},
        ]
        fake_output = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(fake_entries).encode(),
            stderr=b"",
        )

        captured_commands = []

        def mock_call_rclone(cfg, command, pipe_std=False):
            captured_commands.append(command)
            return fake_output

        monkeypatch.setattr(
            rclone,
            "call_rclone_for_central_connection",
            mock_call_rclone,
        )

        folders, files = search_central_via_connection(
            project.cfg,
            None,
            "*",
            return_full_path=return_full_path,
        )

        assert len(folders) == 2
        assert len(files) == 1

        if return_full_path:
            assert all(isinstance(f, Path) for f in folders)
            assert all(isinstance(f, Path) for f in files)
            assert sorted(folders) == [Path("sub-001"), Path("sub-002")]
            assert files == [Path("rawdata.md")]
        else:
            assert all(isinstance(f, str) for f in folders)
            assert all(isinstance(f, str) for f in files)
            assert sorted(folders) == ["sub-001", "sub-002"]
            assert files == ["rawdata.md"]

        assert len(captured_commands) == 1, "Expected exactly one rclone call"
