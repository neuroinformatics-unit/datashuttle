import re

import pytest

from datashuttle.utils_mod import utils


class TestUnit:
    """
    Currently contains misc. unit tests.
    """

    @pytest.mark.parametrize(
        "underscore_position", ["left", "right", "both", "none"]
    )
    @pytest.mark.parametrize("key", ["@DATE", "@TIME", "@DATETIME"])
    def test_datetime_string_replacement(self, key, underscore_position):
        """
        Test the function that replaces @DATE, @TIME or @DATETIME
        keywords with the date / time / datetime. Also, it will
        pre/append underscores to the tags if they are not
        already there (e.g if user input "sub-001@DATE").
        """
        start = "sub-001"
        end = "other-tag"
        name = self.make_name(key, underscore_position, start, end)

        if key == "@DATE":
            regex = re.compile(rf"{start}_date-\d\d\d\d\d\d\d\d_{end}")
        elif key == "@TIME":
            regex = re.compile(rf"{start}_time-\d\d\d\d\d\d_{end}")
        elif key == "@DATETIME":
            regex = re.compile(
                rf"{start}_date-\d\d\d\d\d\d\d\d_time-\d\d\d\d\d\d_{end}"
            )

        name_list = [name]
        utils.update_names_with_datetime(name_list)

        assert re.search(regex, name_list[0]) is not None

    @pytest.mark.parametrize(
        "prefix_and_names",
        [
            ["sub", "sub 001"],
            ["sub", ["sub 001"]],
            ["ses", ["ses- 001", "ses-002"]],
        ],
    )
    def test_spaces_in_process_names(self, prefix_and_names):

        prefix, names = prefix_and_names
        with pytest.raises(BaseException) as e:
            utils.process_names(names, prefix)

        assert str(e.value) == "sub or ses names cannot include spaces."

    # ----------------------------------------------------------------------
    # Utlis
    # ----------------------------------------------------------------------

    def make_name(self, key, underscore_position, start, end):
        """
        Make name with / without underscore to test every
        possibility.
        """
        if underscore_position == "left":
            name = f"{start}_{key}{end}"

        elif underscore_position == "right":
            name = f"{start}{key}_{end}"

        elif underscore_position == "both":
            name = f"{start}_{key}_{end}"

        elif underscore_position == "none":
            name = f"{start}{key}{end}"

        return name
