from pathlib import Path

import pytest

from datashuttle import get_all_sub_and_ses_paths_from_path

from .. import test_utils
from ..base import BaseTest


class TestGetters(BaseTest):
    def test_get_subs_default(self, project):
        """Test project.get_subs() returns sorted subject names by default."""
        assert project.get_subs() == []

        project.create_folders("rawdata", ["sub-003", "sub-001", "sub-002"])

        subs = project.get_subs()
        assert subs == ["sub-001", "sub-002", "sub-003"]

    def test_get_subs_return_full_path(self, project):
        """Test project.get_subs(return_full_path=True) returns list of Path objects."""
        project.create_folders("rawdata", ["sub-001", "sub-002"])

        sub_paths = project.get_subs(return_full_path=True)
        assert len(sub_paths) == 2
        assert all(isinstance(p, Path) for p in sub_paths)
        assert [p.name for p in sub_paths] == ["sub-001", "sub-002"]
        assert all(p.is_dir() for p in sub_paths)

    def test_get_subs_derivatives(self, project):
        """Test project.get_subs(top_level_folder='derivatives') searches derivatives."""
        project.create_folders("rawdata", ["sub-001"])
        project.create_folders("derivatives", ["sub-002", "sub-003"])

        assert project.get_subs("rawdata") == ["sub-001"]
        assert project.get_subs("derivatives") == ["sub-002", "sub-003"]

    def test_get_subs_ignores_non_subject_files_and_folders(self, project):
        """Test project.get_subs() ignores non-subject files and directories."""
        project.create_folders("rawdata", ["sub-001", "sub-002"])

        rawdata_path = project.cfg["local_path"] / "rawdata"
        (rawdata_path / "notes.txt").write_text("experimental notes")
        (rawdata_path / ".DS_Store").write_text("system file")
        (rawdata_path / "calibration_data").mkdir(parents=True, exist_ok=True)

        subs = project.get_subs()
        assert subs == ["sub-001", "sub-002"]

    def test_get_subs_include_central(self, tmp_path, clean_project_name):
        """Test project.get_subs(include_central=True) combines local and central subjects."""
        project = test_utils.setup_project_default_configs(
            clean_project_name,
            tmp_path,
            local_path=tmp_path / "local" / clean_project_name,
            central_path=tmp_path / "central" / clean_project_name,
        )

        # Create sub-001 locally
        project.create_folders("rawdata", ["sub-001"])

        # Manually create sub-002 on central
        central_sub = project.cfg["central_path"] / "rawdata" / "sub-002"
        central_sub.mkdir(parents=True, exist_ok=True)

        assert project.get_subs(include_central=False) == ["sub-001"]
        assert project.get_subs(include_central=True) == ["sub-001", "sub-002"]

    def test_get_ses_default(self, project):
        """Test project.get_ses() returns sorted session names for a given subject."""
        project.create_folders(
            "rawdata",
            sub_names="sub-001",
            ses_names=["ses-003", "ses-001", "ses-002"],
        )

        assert project.get_ses("sub-001") == ["ses-001", "ses-002", "ses-003"]

    def test_get_ses_without_sub_prefix(self, project):
        """Test project.get_ses() formats subject name if passed without 'sub-' prefix."""
        project.create_folders(
            "rawdata",
            sub_names="sub-001",
            ses_names=["ses-001", "ses-002"],
        )

        assert project.get_ses("001") == ["ses-001", "ses-002"]

    def test_get_ses_subject_with_custom_tags(self, project):
        """Test project.get_ses() resolves sessions when subject folder has custom key-value tags."""
        rawdata_path = project.cfg["local_path"] / "rawdata"
        tagged_sub_path = rawdata_path / "sub-001_id-mouse123_date-20261102"
        (tagged_sub_path / "ses-001").mkdir(parents=True, exist_ok=True)
        (tagged_sub_path / "ses-002").mkdir(parents=True, exist_ok=True)

        assert project.get_ses("sub-001") == ["ses-001", "ses-002"]
        assert project.get_ses("001") == ["ses-001", "ses-002"]
        assert project.get_ses("sub-001_id-mouse123_date-20261102") == [
            "ses-001",
            "ses-002",
        ]

    def test_get_datatype_folders(self, project):
        """Test project.get_datatype_folders() retrieves existing datatype folders."""
        project.create_folders(
            "rawdata",
            sub_names="sub-001",
            ses_names="ses-001",
            datatype=["ephys", "behav"],
        )

        dtypes = project.get_datatype_folders("sub-001", "ses-001")
        assert dtypes == ["behav", "ephys"]

        dtype_paths = project.get_datatype_folders(
            "sub-001", "ses-001", return_full_path=True
        )
        assert len(dtype_paths) == 2
        assert all(isinstance(p, Path) for p in dtype_paths)
        assert [p.name for p in dtype_paths] == ["behav", "ephys"]

    def test_get_all_sub_and_ses_alias(self, project):
        """Test project.get_all_sub_and_ses() alias matches get_all_sub_and_ses_paths()."""
        project.create_folders(
            "rawdata",
            sub_names="sub-001",
            ses_names=["ses-001", "ses-002"],
        )

        res1 = project.get_all_sub_and_ses_paths()
        res2 = project.get_all_sub_and_ses()
        assert res1 == res2

    def test_get_ses_return_full_path(self, project):
        """Test project.get_ses(return_full_path=True) returns list of Path objects."""
        project.create_folders(
            "rawdata",
            sub_names="sub-001",
            ses_names=["ses-001", "ses-002"],
        )

        ses_paths = project.get_ses("sub-001", return_full_path=True)
        assert len(ses_paths) == 2
        assert all(isinstance(p, Path) for p in ses_paths)
        assert [p.name for p in ses_paths] == ["ses-001", "ses-002"]
        assert all(p.is_dir() for p in ses_paths)

    def test_get_ses_empty(self, project):
        """Test project.get_ses() returns empty list when subject has no sessions."""
        project.create_folders("rawdata", sub_names="sub-001")

        assert project.get_ses("sub-001") == []

    def test_get_all_sub_and_ses_paths_instance_method(self, project):
        """Test project.get_all_sub_and_ses_paths() returns complete mapping."""
        project.create_folders(
            "rawdata",
            sub_names="sub-001",
            ses_names=["ses-001", "ses-002"],
        )
        project.create_folders(
            "rawdata",
            sub_names="sub-002",
            ses_names=["ses-001"],
        )

        result = project.get_all_sub_and_ses_paths("rawdata")
        assert "sub" in result
        assert "ses" in result

        sub_names = [p.name for p in result["sub"]]
        assert sub_names == ["sub-001", "sub-002"]

        assert [p.name for p in result["ses"]["sub-001"]] == [
            "ses-001",
            "ses-002",
        ]
        assert [p.name for p in result["ses"]["sub-002"]] == ["ses-001"]

    def test_get_all_sub_and_ses_paths_from_path_standalone(self, tmp_path):
        """Test get_all_sub_and_ses_paths_from_path directly on a folder without datashuttle configs."""
        project_dir = tmp_path / "standalone_nbp_project"
        rawdata_dir = project_dir / "rawdata"

        # Create folders manually without DataShuttle configs (Issue #704)
        (rawdata_dir / "sub-01" / "ses-01").mkdir(parents=True, exist_ok=True)
        (rawdata_dir / "sub-01" / "ses-02").mkdir(parents=True, exist_ok=True)
        (rawdata_dir / "sub-02" / "ses-01").mkdir(parents=True, exist_ok=True)

        result = get_all_sub_and_ses_paths_from_path(project_dir, "rawdata")

        assert [p.name for p in result["sub"]] == ["sub-01", "sub-02"]
        assert [p.name for p in result["ses"]["sub-01"]] == [
            "ses-01",
            "ses-02",
        ]
        assert [p.name for p in result["ses"]["sub-02"]] == ["ses-01"]

    def test_get_all_sub_and_ses_paths_from_path_both_top_level(
        self, tmp_path
    ):
        """Test get_all_sub_and_ses_paths_from_path with top_level_folder=None searches both."""
        project_dir = tmp_path / "multi_toplevel_project"
        (project_dir / "rawdata" / "sub-01" / "ses-01").mkdir(
            parents=True, exist_ok=True
        )
        (project_dir / "derivatives" / "sub-02" / "ses-01").mkdir(
            parents=True, exist_ok=True
        )

        result = get_all_sub_and_ses_paths_from_path(
            project_dir, top_level_folder=None
        )

        assert [p.name for p in result["sub"]] == ["sub-01", "sub-02"]
        assert "sub-01" in result["ses"]
        assert "sub-02" in result["ses"]

    def test_get_all_sub_and_ses_paths_from_path_non_existent(self, tmp_path):
        """Test get_all_sub_and_ses_paths_from_path raises FileNotFoundError for non-existent path."""
        non_existent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError) as exc_info:
            get_all_sub_and_ses_paths_from_path(non_existent)
        assert "Cannot get paths. No directory found" in str(exc_info.value)
