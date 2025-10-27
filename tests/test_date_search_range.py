import pytest

from datashuttle.configs import canonical_tags

from . import test_utils
from .base import BaseTest


class TestDateSearchRange(BaseTest):
    """Test date/time range search functionality with real datashuttle projects."""

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_date_range_transfer(self, project, upload_or_download):
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
        datatypes_used.update({"behav": True})

        test_utils.make_and_check_local_project_folders(
            project,
            "rawdata",
            subs,
            sessions,
            ["behav"],
            datatypes_used,
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(
            project, upload_or_download, "custom", "rawdata"
        )

        transfer_function(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240315{canonical_tags.tags('DATETO')}20240401"
            ],
            datatype=["behav"],
        )

        path_to_check = base_path_to_check / "rawdata"
        transferred_subs = list(path_to_check.glob("sub-*"))

        assert len(transferred_subs) == 2

        for sub_path in transferred_subs:
            transferred_sessions = [ses.name for ses in sub_path.glob("ses-*")]
            expected_sessions = [
                "ses-002_date-20240315",
                "ses-003_date-20240401",
            ]
            assert sorted(transferred_sessions) == sorted(expected_sessions)

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_time_range_transfer(self, project, upload_or_download):
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

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(
            project, upload_or_download, "custom", "rawdata"
        )

        transfer_function(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_100000{canonical_tags.tags('TIMETO')}180000"
            ],
            datatype=["behav"],
        )

        path_to_check = base_path_to_check / "rawdata" / "sub-001"
        transferred_sessions = [
            ses.name for ses in path_to_check.glob("ses-*")
        ]

        expected_sessions = ["ses-002_time-120000", "ses-003_time-160000"]
        assert sorted(transferred_sessions) == sorted(expected_sessions)

    @pytest.mark.parametrize("upload_or_download", ["upload", "download"])
    def test_datetime_range_transfer(self, project, upload_or_download):
        """Test that wildcard matching works with datetime-tagged sessions."""
        subs = ["sub-001"]
        sessions = [
            "ses-001_datetime-20240301T080000",
            "ses-002_datetime-20240315T120000",
            "ses-003_datetime-20240401T160000",
            "ses-004_datetime-20240401T160001",
            "ses-005_datetime-20240415T200000",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        (
            transfer_function,
            base_path_to_check,
        ) = test_utils.handle_upload_or_download(
            project, upload_or_download, "custom", "rawdata"
        )

        transfer_function(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-{canonical_tags.tags('*')}_20240315T120000{canonical_tags.tags('DATETIMETO')}20240401T160002",
                f"ses-{canonical_tags.tags('*')}_20240415T200000{canonical_tags.tags('DATETIMETO')}20240415T200000",
            ],
            datatype=["all"],
        )

        path_to_check = base_path_to_check / "rawdata" / "sub-001"
        transferred_sessions = [
            ses.name for ses in path_to_check.glob("ses-*")
        ]

        expected_sessions = [
            "ses-002_datetime-20240315T120000",
            "ses-003_datetime-20240401T160000",
            "ses-004_datetime-20240401T160001",
            "ses-005_datetime-20240415T200000",
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

        with pytest.raises(Exception) as e:
            project.upload_custom(
                "rawdata",
                sub_names=subs,
                ses_names=[
                    f"ses-{canonical_tags.tags('*')}_20240401{canonical_tags.tags('DATETO')}20240301"
                ],
                datatype=["behav"],
            )

        assert "End date is before start date." in str(e.value)

        with pytest.raises(Exception) as e:
            project.upload_custom(
                "rawdata",
                sub_names=subs,
                ses_names=[
                    f"ses-{canonical_tags.tags('*')}_2024030{canonical_tags.tags('DATETO')}20240401"
                ],
                datatype=["behav"],
            )
        assert "Invalid" in str(e.value)

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

    def test_subject_level_ranges(self, project):
        """Test date, time and datetime ranges at the subject level."""
        subs = [
            "sub-001_date-20240301",
            "sub-002_date-20240315",
            "sub-003_date-20240401",
            "sub-004_date-20240415",
            "sub-005_time-020101_id-123",
            "sub-006_time-090101_id-123",
            "sub-007_time-130523_id-123",
            "sub-008_time-130525_id-123",
            "sub-009_datetime-20240301T020101_id-123",
            "sub-010_datetime-20240301T020105_id-123",
            "sub-011_datetime-20240506T110101_id-123",
            "sub-012_datetime-20240508T110101_id-123",
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
                f"sub-{canonical_tags.tags('*')}_20240310{canonical_tags.tags('DATETO')}20240410",
                f"sub-{canonical_tags.tags('*')}_090100{canonical_tags.tags('TIMETO')}130524{canonical_tags.tags('*')}",
                f"sub-{canonical_tags.tags('*')}_20240301T020104{canonical_tags.tags('DATETIMETO')}20240506T110701{canonical_tags.tags('*')}",
            ],
            ses_names=sessions,
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata"
        transferred_subs = [sub.name for sub in central_path.glob("sub-*")]

        expected_subs = [
            "sub-002_date-20240315",
            "sub-003_date-20240401",
            "sub-006_time-090101_id-123",
            "sub-007_time-130523_id-123",
            "sub-010_datetime-20240301T020105_id-123",
            "sub-011_datetime-20240506T110101_id-123",
        ]

        assert sorted(transferred_subs) == sorted(expected_subs)

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

    def test_with_range_to_flag(self, project):
        """Test that the @DATETO@ works well with @TO@"""
        subs = ["sub-001"]

        sessions = [
            "ses-001_date-20240301",
            "ses-002_date-20240301",
            "ses-003_date-20240405",
            "ses-004_date-20240415",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        # Select such that ses-002 onwards is selected, and
        # ses-004 is excluded based on date.
        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-002@TO@004_20240301{canonical_tags.tags('DATETO')}20240406"
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata" / "sub-001"
        transferred_sessions = [ses.name for ses in central_path.glob("ses-*")]

        expected_sessions = [
            "ses-002_date-20240301",
            "ses-003_date-20240405",
        ]
        assert sorted(transferred_sessions) == sorted(expected_sessions)

    def test_without_wildcard_ses(self, project):
        """Test without wildcard ses.

        Including @*@ only led to an uncaught but as it was triggering a
        conditional in `check_and_format_names` that was not triggered by
        @DATETO@ alone though it should have been.
        """
        subs = ["sub-001"]

        sessions = [
            "ses-001_date-20240301",
            "ses-002_date-20240301",
            "ses-003_date-20240405",
            "ses-004_date-20240415",
        ]

        datatypes_used = test_utils.get_all_broad_folders_used(value=False)
        datatypes_used.update({"behav": True})
        test_utils.make_and_check_local_project_folders(
            project, "rawdata", subs, sessions, ["behav"], datatypes_used
        )

        # Select such that ses-002 is selected (and it is in range)
        project.upload_custom(
            "rawdata",
            sub_names=subs,
            ses_names=[
                f"ses-002_20240301{canonical_tags.tags('DATETO')}20240302"
            ],
            datatype=["behav"],
        )

        central_path = project.get_central_path() / "rawdata" / "sub-001"
        transferred_sessions = [ses.name for ses in central_path.glob("ses-*")]

        expected_sessions = [
            "ses-002_date-20240301",
        ]
        assert sorted(transferred_sessions) == sorted(expected_sessions)
