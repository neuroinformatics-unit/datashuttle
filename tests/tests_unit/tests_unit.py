import re

import pytest

from datashuttle.configs.canonical_directories_and_tags import tags
from datashuttle.utils import formatting, utils


class TestUnit:
    """
    Currently contains misc. unit tests.
    """

    @pytest.mark.parametrize(
        "underscore_position", ["left", "right", "both", "none"]
    )
    @pytest.mark.parametrize(
        "key", [tags("date"), tags("time"), tags("datetime")]
    )
    def test_datetime_string_replacement(self, key, underscore_position):
        """
        Test the function that replaces @DATE, @TIME@ or @DATETIME@
        keywords with the date / time / datetime. Also, it will
        pre/append underscores to the tags if they are not
        already there (e.g if user input "sub-001@DATE").
        """
        start = "sub-001"
        end = "other-tag"
        name = self.make_name(key, underscore_position, start, end)

        if key == tags("date"):
            regex = re.compile(rf"{start}_date-\d\d\d\d\d\d\d\d_{end}")
        elif key == tags("time"):
            regex = re.compile(rf"{start}_time-\d\d\d\d\d\d_{end}")
        elif key == tags("datetime"):
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
    def test_spaces_in_format_names(self, prefix_and_names):

        prefix, names = prefix_and_names
        with pytest.raises(BaseException) as e:
            formatting.format_names(names, prefix)

        assert str(e.value) == "sub or ses names cannot include spaces."

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_process_to_keyword_in_sub_input(self, prefix):
        """ """
        results = utils.update_names_with_range_to_flag(
            [f"{prefix}-001", f"{prefix}-01{tags('to')}123"], prefix
        )
        assert results == [f"{prefix}-001"] + [
            f"{prefix}-{str(num).zfill(2)}" for num in range(1, 124)
        ]

        results = utils.update_names_with_range_to_flag(
            [f"{prefix}-1{tags('to')}3_hello-world"], prefix
        )
        assert results == [
            f"{prefix}-1_hello-world",
            f"{prefix}-2_hello-world",
            f"{prefix}-3_hello-world",
        ]

        results = utils.update_names_with_range_to_flag(
            [
                f"{prefix}-01{tags('to')}3_hello",
                f"{prefix}-4{tags('to')}005_goodbye",
                f"{prefix}-006{tags('to')}0007_hello",
            ],
            prefix,
        )

        assert results == [
            f"{prefix}-01_hello",
            f"{prefix}-02_hello",
            f"{prefix}-03_hello",
            f"{prefix}-004_goodbye",
            f"{prefix}-005_goodbye",
            f"{prefix}-0006_hello",
            f"{prefix}-0007_hello",
        ]

    @pytest.mark.parametrize("prefix", ["sub-", "ses-"])
    @pytest.mark.parametrize(
        "bad_input",
        [
            f"1{tags('to')}2",
            f"prefix-1{tags('to')}_date",
            f"prefix-@01{tags('to')}02",
            f"prefix-01{tags('to')}1M1",
        ],
    )
    def test_process_to_keyword_bad_input_raises_error(
        self, prefix, bad_input
    ):

        bad_input = bad_input.replace("prefix", prefix)

        with pytest.raises(BaseException) as e:
            utils.update_names_with_range_to_flag([bad_input], prefix)

        assert (
            str(e.value)
            == f"The name: {bad_input} is not in required format for {tags('to')} keyword. "
            f"The start must be  be {prefix}<NUMBER>{tags('to')}<NUMBER>)"
        )

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
