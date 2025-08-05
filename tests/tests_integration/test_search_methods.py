from pathlib import Path

from .. import test_utils
from ..base import BaseTest

# -----------------------------------------------------------------------------
# Inconsistent sub or ses value lengths
# -----------------------------------------------------------------------------


class TestSubSesSearches(BaseTest):
    def test_local_vs_central_search_methods(self, project, monkeypatch):
        """ """
        central_path = project.get_central_path()

        paths_to_make = []
        for i in range(1, 4):
            paths_to_make.append(Path(f"rawdata/sub-00{i}/ses-001/behav"))
            paths_to_make.append(
                Path(f"rawdata/sub-00{i}/ses-002_date-20250402/behav")
            )
            paths_to_make.append(
                Path(f"rawdata/sub-00{i}/ses-002_date-20250402/anat")
            )

        paths_to_make.append(
            Path("rawdata/sub-003_condition-test/ses-001_hello-world/ephys")
        )
        paths_to_make.append(
            Path("rawdata/sub-004_condition-test/ses-002_hello-world/funcimg")
        )

        for path_ in paths_to_make:
            (central_path / path_).mkdir(parents=True)
            breakpoint()
            test_utils.write_file(
                central_path / path_ / f"{path_.name}.md",
                contents="hello_world",
            )
            test_utils.write_file(
                central_path / path_.parent / f"{path_.parent.name}.md",
                contents="hello_world",
            )
            test_utils.write_file(
                central_path
                / path_.parent.parent
                / f"{path_.parent.parent.name}.md",
                contents="hello_world",
            )

        from datashuttle.utils.folders import (
            search_central_via_connection,
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

        hello, world = search_central_via_connection(
            project.cfg,
            central_path / "rawdata",
            "sub-*",
            return_full_path=True,
        )

        breakpoint()
