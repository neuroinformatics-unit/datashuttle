import re

import pytest

from datashuttle.configs.canonical_tags import tags
from datashuttle.utils import formatting, getters, utils


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
        Note cannot use regex \d{8} format because we are in an
        f-string.
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
                rf"{start}_datetime-\d\d\d\d\d\d\d\dT\d\d\d\d\d\d_{end}"
            )

        name_list = [name]
        formatting.update_names_with_datetime(name_list)

        assert (
            re.search(regex, name_list[0]) is not None
        ), "datetime formatting is incorrect."

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_process_to_keyword_in_sub_input(self, prefix):
        """ """
        results = formatting.update_names_with_range_to_flag(
            [f"{prefix}-001", f"{prefix}-01{tags('to')}123"], prefix
        )
        assert results == [f"{prefix}-001"] + [
            f"{prefix}-{str(num).zfill(2)}" for num in range(1, 124)
        ]

        results = formatting.update_names_with_range_to_flag(
            [f"{prefix}-1{tags('to')}3_hello-world"], prefix
        )
        assert results == [
            f"{prefix}-1_hello-world",
            f"{prefix}-2_hello-world",
            f"{prefix}-3_hello-world",
        ]

        results = formatting.update_names_with_range_to_flag(
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

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
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

        with pytest.raises(ValueError) as e:
            formatting.update_names_with_range_to_flag([bad_input], prefix)

        assert (
            str(e.value) == f"The name: {bad_input} is not in required"
            f" format for {tags('to')} keyword. "
            f"The start must be  be {prefix}-<NUMBER>{tags('to')}<NUMBER>)."
        )

    def test_get_value_from_bids_name_regexp(self):
        """
        Test the regexp that finds the value from a BIDS-name
        key-value pair.
        """
        bids_name = "sub-0123125_ses-11312_datetime-5345323_id-3asd@523"

        sub = utils.get_value_from_key_regexp(bids_name, "sub")[0]
        assert sub == "0123125"

        ses = utils.get_value_from_key_regexp(bids_name, "ses")[0]
        assert ses == "11312"

        datetime = utils.get_value_from_key_regexp(bids_name, "datetime")[0]
        assert datetime == "5345323"

        id = utils.get_value_from_key_regexp(bids_name, "id")[0]
        assert id == "3asd@523"

    def test_num_leading_zeros(self):
        """
        Check num_leading_zeros handles prefixed and non-prefixed
        case from -1 to -(101x 0)1.
        """
        for i in range(101):
            assert utils.num_leading_zeros("1".zfill(i + 1)) == i
            assert utils.num_leading_zeros("sub-" + "1".zfill(i + 1)) == i
            assert utils.num_leading_zeros("ses-" + "1".zfill(i + 1)) == i

    # Test getting max sub or ses num from list
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    @pytest.mark.parametrize("default_num_value_digits", [0, 1, 11, 99, 101])
    def test_get_max_sub_or_ses_num_and_value_length_empty(
        self, prefix, default_num_value_digits
    ):
        """
        When the list of sub or ses names is empty, the returned max number
        should be zero and the `default_num_value_digits`
        be set to the passed default
        """
        (
            max_value,
            num_digits,
        ) = getters.get_max_sub_or_ses_num_and_value_length(
            [], prefix, default_num_value_digits
        )

        assert max_value == 0
        assert num_digits == default_num_value_digits

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_get_max_sub_or_ses_num_and_value_length_error(self, prefix):
        """
        An error will be shown if the sub or ses value digits are inconsistent,
        because it is not possible to return the number of values required.

        A warning should be shown in that the number of value digits are
        inconsistent, as the user may be confused as to the real max.
        """
        bad_num_values_names = [
            f"{prefix}-001",
            f"{prefix}-02",
            f"{prefix}-003",
        ]

        with pytest.raises(BaseException) as e:
            getters.get_max_sub_or_ses_num_and_value_length(
                bad_num_values_names, prefix
            )

        assert (
            f"The number of value digits for the {prefix} "
            f"level are not consistent." in str(e.value)
        )

        bad_sub_num_names = [
            f"{prefix}-0001",
            f"{prefix}-0002",
            f"{prefix}-0004",
            f"{prefix}-0005",
        ]

        with pytest.warns(UserWarning) as w:
            (
                max_num,
                num_digits,
            ) = getters.get_max_sub_or_ses_num_and_value_length(
                bad_sub_num_names, prefix
            )

        assert (
            "A subject number has been skipped, currently used subject "
            "numbers are: [1, 2, 4, 5]" in str(w[0].message)
        )
        assert max_num == 5
        assert num_digits == 4

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    @pytest.mark.parametrize("test_num_digits", [1, 4, 11])
    @pytest.mark.parametrize("test_max_num", [1, 9, 99, 101])
    def test_get_max_sub_or_ses_num_and_value_length(
        self, prefix, test_max_num, test_num_digits
    ):
        """
        Test many combinations of subject names
        and number of digits for a project,
        e.g. `names = ["sub-001", ... "sub-101"]`.
        """
        if test_num_digits < (max_len := len(str(test_max_num))):
            test_num_digits = max_len

        names = []
        for value in range(test_max_num + 1):
            format_name = f"{prefix}-{str(value).zfill(test_num_digits)}"
            names.append(format_name)

        max_num, num_digits = getters.get_max_sub_or_ses_num_and_value_length(
            names, prefix
        )

        assert max_num == test_max_num
        assert num_digits == test_num_digits

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_get_max_sub_or_ses_num_and_value_length_edge_case(self, prefix):
        """
        Test the edge case where the subject number does not start at 1.
        """
        names = [f"{prefix}-09", f"{prefix}-10", f"{prefix}-11"]

        max_num, num_digits = getters.get_max_sub_or_ses_num_and_value_length(
            names, prefix
        )

        assert max_num == 11
        assert num_digits == 2

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

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
