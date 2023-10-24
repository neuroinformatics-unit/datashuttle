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
