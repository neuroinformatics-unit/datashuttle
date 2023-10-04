import os.path
import shutil
import warnings

import pytest
from base import BaseTest

from datashuttle.utils import formatting


class TestFormatting(BaseTest):
    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    @pytest.mark.parametrize(
        "input", [1, {"test": "one"}, 1.0, ["1", "2", ["three"]]]
    )
    def test_format_names_bad_input(self, input, prefix):
        """
        Test that names passed in incorrect type
        (not str, list) raise appropriate error.
        """
        with pytest.raises(BaseException) as e:
            formatting.format_names(input, prefix)

        assert (
            "Ensure subject and session names are "
            "list of strings, or string" == str(e.value)
        )

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_format_names_duplicate_ele(self, prefix):
        """
        Test that appropriate error is raised when duplicate name
        is passed to format_names().
        """
        with pytest.raises(BaseException) as e:
            formatting.format_names(["1", "2", "3", "3", "4"], prefix)

        assert (
            "Subject and session names but all be unique "
            "(i.e. there are no duplicates in list input)." == str(e.value)
        )

    def test_format_names_prefix(self):
        """
        Check that format_names correctly prefixes input
        with default sub or ses prefix. This is less useful
        now that ses/sub name dash and underscore order is
        more strictly checked.
        """
        prefix = "sub"

        # check name is prefixed
        formatted_names = formatting.format_names("1", prefix)
        assert formatted_names[0] == "sub-1"

        # check existing prefix is not duplicated
        formatted_names = formatting.format_names("sub-1", prefix)
        assert formatted_names[0] == "sub-1"

        # test mixed list of prefix and unprefixed are prefixed correctly.
        mixed_names = ["1", prefix + "-four", "5", prefix + "-6"]
        formatted_names = formatting.format_names(mixed_names, prefix)
        assert formatted_names == [
            "sub-1",
            "sub-four",
            "sub-5",
            "sub-6",
        ]

    def test_warning_non_consecutive_numbers(self, project):
        project.make_folders(
            ["sub-01", "sub-2", "sub-04"], ["ses-05", "ses-10"]
        )

        with pytest.warns(UserWarning) as w:
            project.get_next_sub_number()
        assert (
            str(w[0].message) == "A subject number has been skipped, "
            "currently used subject numbers are: [1, 2, 4]"
        )

        with pytest.warns(UserWarning) as w:
            project.get_next_ses_number("sub-2")
        assert (
            str(w[0].message)
            == "A subject number has been skipped, currently "
            "used subject numbers are: [5, 10]"
        )

    @pytest.mark.parametrize(
        "bad_sub_name",
        ["sub-03_date-123", "sub-0003_id-123", "sub-0999", "sub-0034"],
    )
    def test_warn_on_inconsistent_leading_zeros_subjects(
        self, project, bad_sub_name
    ):
        project.make_sub_folders(
            ["sub-001", "sub-010", "sub-100_date-20221314", "sub-1000"],
            ["ses-001_id-1231"],
        )

        self.run_warn_on_consistentent_leading_zeros_sub_or_ses(
            project,
            bad_sub_name,
            "ses-002",  # an innocuous ses-name, placeholder.
        )

    @pytest.mark.parametrize(
        "bad_ses_name",
        ["ses-03_date-123", "ses-0003_id-123", "ses-0999", "ses-0034"],
    )
    def test_warn_on_inconsistent_leading_zeros_sessions(
        self, project, bad_ses_name
    ):
        # TODO: check with breakpints this is doing exactly what is expected!!!
        # TODO: should probably check these are raised at the actual
        # transfer / start up function not in this lower-level function.
        project.make_sub_folders(
            ["sub-001", "sub-002"],
            [
                "ses-001_id-1231",
                "ses-020_date-123123" "ses-200",
                "ses-2000_id-12312",
            ],
        )

        self.run_warn_on_consistentent_leading_zeros_sub_or_ses(
            project,
            "sub-002",
            bad_ses_name,  # an innocuous sub-name, placeholder.
        )

    def run_warn_on_consistentent_leading_zeros_sub_or_ses(
        self, project, sub_name, ses_name
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            project._show_pre_transfer_messages()

        project.make_sub_folders(sub_name, ses_name)

        self.check_inconsistent_sub_or_ses_level_warning(project, "sub")

        project.upload_all()
        shutil.rmtree(project.cfg.get_base_folder("local") / sub_name)

        self.check_inconsistent_sub_or_ses_level_warning(project, "sub")

    def check_inconsistent_sub_or_ses_level_warning(self, project, sub_or_ses):
        with pytest.warns(UserWarning) as w:
            project._show_pre_transfer_messages()

        assert (
            str(w[0].message) == f"Inconsistent number of leading zeros for "
            f"{sub_or_ses} names in the project found. It is "
            f"crucial these are made consistent as "
            f"soon as possible to avoid unexpected "
            f"behaviour of DataShuttle during data transfer."
        )
