import os
import shutil

import pytest

from datashuttle.configs import canonical_tags

from . import test_utils
from .base import BaseTest


class TestDateSearchRange(BaseTest):
    """Test date/time range search functionality with real datashuttle projects."""

    def test_simple_wildcard_first(self, project):
        """Test basic wildcard functionality before testing date ranges."""
        subs = ["sub-001", "sub-002"]
        sessions = ["ses-001", "ses-002"]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=[f"sub-{canonical_tags.tags('*')}"],
            ses_names=[f"ses-{canonical_tags.tags('*')}"],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata"
        transferred_subs = [sub.name for sub in central_path.glob("sub-*")]

        expected_subs = ["sub-001", "sub-002"]
        assert sorted(transferred_subs) == sorted(expected_subs)

        for sub_name in expected_subs:
            sub_path = central_path / sub_name
            transferred_sessions = [ses.name for ses in sub_path.glob("ses-*")]
            expected_sessions = ["ses-001", "ses-002"]
            assert sorted(transferred_sessions) == sorted(expected_sessions)

    def test_date_range_transfer(self, project):
        """Test that date range patterns correctly filter folders during transfer."""
        subs = ["sub-001", "sub-002"]
        sessions = [
            "ses-001_date-20240301",
            "ses-002_date-20240315",
            "ses-003_date-20240401",
            "ses-004_date-20240415",
            "ses-005_date-20240501",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True, "ephys": True})
        test_utils.make_and_check_local_project_folders(
            project,
            "rawdata",
            subs,
            sessions,
            ["behav", "ephys"],
            datatypes_used,
        )

        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240315{canonical_tags.tags('DATETO')}20240401"
            ],
            datatype=["behav", "ephys"],
        )

        central_path = project.get_central_path() / "rawdata"
        transferred_subs = list(central_path.glob("sub-*"))

        assert len(transferred_subs) == 2

        for sub_path in transferred_subs:
            transferred_sessions = [ses.name for ses in sub_path.glob("ses-*")]
            expected_sessions = [
                "ses-002_date-20240315",
                "ses-003_date-20240401",
            ]
            assert sorted(transferred_sessions) == sorted(expected_sessions)

    def test_time_range_transfer(self, project):
        """Test that time range patterns work correctly."""
        subs = ["sub-001"]
        sessions = [
            "ses-001_time-080000",
            "ses-002_time-120000",
            "ses-003_time-160000",
            "ses-004_time-200000",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_100000{canonical_tags.tags('TIMETO')}180000"
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata" / "sub-001"
        transferred_sessions = [ses.name for ses in central_path.glob("ses-*")]

        expected_sessions = ["ses-002_time-120000", "ses-003_time-160000"]
        assert sorted(transferred_sessions) == sorted(expected_sessions)

    def test_datetime_range_transfer(self, project):
        """Test that wildcard matching works with datetime-tagged sessions."""
        subs = ["sub-001"]
        sessions = [
            "ses-001_datetime-20240301T080000",
            "ses-002_datetime-20240315T120000",
            "ses-003_datetime-20240401T160000",
            "ses-004_datetime-20240415T200000",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_datetime-20240315{canonical_tags.tags('*')}",
                f"ses-{canonical_tags.tags('*')}_datetime-20240401{canonical_tags.tags('*')}",
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata" / "sub-001"
        transferred_sessions = [ses.name for ses in central_path.glob("ses-*")]

        expected_sessions = [
            "ses-002_datetime-20240315T120000",
            "ses-003_datetime-20240401T160000",
        ]
        assert sorted(transferred_sessions) == sorted(expected_sessions)

    def test_combined_wildcard_and_date_range(self, project):
        """Test combining wildcards with date ranges."""
        subs = ["sub-001", "sub-002", "sub-003"]
        sessions = [
            "ses-001_date-20240301_run-01",
            "ses-002_date-20240315_run-02",
            "ses-003_date-20240401_run-01",
            "ses-004_date-20240415_run-03",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=[f"sub-{canonical_tags.tags('*')}"],
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240310{canonical_tags.tags('DATETO')}20240420_run-01",
                f"ses-{canonical_tags.tags('*')}_20240310{canonical_tags.tags('DATETO')}20240420_run-02",
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata"
        transferred_subs = list(central_path.glob("sub-*"))

        assert len(transferred_subs) == 3

        for sub_path in transferred_subs:
            transferred_sessions = [ses.name for ses in sub_path.glob("ses-*")]
            expected_sessions = [
                "ses-002_date-20240315_run-02",
                "ses-003_date-20240401_run-01",
            ]
            assert sorted(transferred_sessions) == sorted(expected_sessions)

    def test_invalid_date_range_errors(self, project):
        """Test that invalid date ranges raise appropriate errors."""
        subs = ["sub-001"]
        sessions = ["ses-001_date-20240301"]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        with pytest.raises(Exception) as exc_info:
            project.upload_custom(
                "rawdata",
                sub_names=subs,
                ses_names=[
                    f"ses-{canonical_tags.tags('*')}_20240401{canonical_tags.tags('DATETO')}20240301"
                ],
                datatype=["behav"],
            )
        assert "before start" in str(exc_info.value)

        with pytest.raises(Exception) as exc_info:
            project.upload_custom(
                "rawdata",
                sub_names=subs,
                ses_names=[
                    f"ses-{canonical_tags.tags('*')}_2024030{canonical_tags.tags('DATETO')}20240401"
                ],
                datatype=["behav"],
            )
        assert "Invalid" in str(exc_info.value)

    def test_no_matches_in_date_range(self, project):
        """Test behavior when no folders match the date range."""
        subs = ["sub-001"]
        sessions = [
            "ses-001_date-20240101",
            "ses-002_date-20240201",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240301{canonical_tags.tags('DATETO')}20240401"
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata"
        transferred_items = list(central_path.glob("*"))

        if transferred_items:
            transferred_sub_names = [
                item.name
                for item in transferred_items
                if item.name.startswith("sub-")
            ]
            assert len(transferred_sub_names) == 0

    def test_subject_level_date_range(self, project):
        """Test date ranges work at the subject level too."""
        subs = [
            "sub-001_date-20240301",
            "sub-002_date-20240315",
            "sub-003_date-20240401",
            "sub-004_date-20240415",
        ]
        sessions = ["ses-001"]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=[
                f"sub-{canonical_tags.tags('*')}_20240310{canonical_tags.tags('DATETO')}20240410"
            ],
            ses_names=sessions,
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata"
        transferred_subs = [sub.name for sub in central_path.glob("sub-*")]

        expected_subs = ["sub-002_date-20240315", "sub-003_date-20240401"]
        assert sorted(transferred_subs) == sorted(expected_subs)

    @pytest.mark.parametrize("project", ["full"], indirect=True)
    def test_download_with_date_range(self, project):
        """Test that date range patterns work for downloads as well as uploads."""
        subs = ["sub-001", "sub-002"]
        sessions = [
            "ses-001_date-20240301",
            "ses-002_date-20240315",
            "ses-003_date-20240401",
            "ses-004_date-20240415",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=sessions,
            datatype=["behav"],
        )

        os.chdir(project.get_local_path())
        local_rawdata = project.get_local_path() / "rawdata"
        if local_rawdata.exists():
            shutil.rmtree(local_rawdata)

        project.download_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240310{canonical_tags.tags('DATETO')}20240401"
            ],
            datatype=["behav"],
        )

        local_path = project.get_local_path() / "rawdata"
        downloaded_subs = list(local_path.glob("sub-*"))

        assert len(downloaded_subs) == 2

        for sub_path in downloaded_subs:
            downloaded_sessions = [ses.name for ses in sub_path.glob("ses-*")]
            expected_sessions = [
                "ses-002_date-20240315",
                "ses-003_date-20240401",
            ]
            assert sorted(downloaded_sessions) == sorted(expected_sessions)

    def test_edge_case_exact_boundary_dates(self, project):
        """Test that boundary dates are handled correctly (inclusive ranges)."""
        subs = ["sub-001"]
        sessions = [
            "ses-001_date-20240301",
            "ses-002_date-20240315",
            "ses-003_date-20240401",
            "ses-004_date-20240415",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240301{canonical_tags.tags('DATETO')}20240401"
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata" / "sub-001"
        transferred_sessions = [ses.name for ses in central_path.glob("ses-*")]

        expected_sessions = [
            "ses-001_date-20240301",
            "ses-002_date-20240315",
            "ses-003_date-20240401",
        ]
        assert sorted(transferred_sessions) == sorted(expected_sessions)
