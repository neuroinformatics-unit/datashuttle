import pytest

from datashuttle.utils import formatting, validation


class TestValidationUnit:
    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_more_than_one_instance(self, prefix):
        """
        Check that any duplicate sub or ses values are caught
        in `validate_list_of_names()`.
        """
        with pytest.raises(BaseException) as e:
            validation.validate_list_of_names(
                [f"{prefix}-001", f"{prefix}-99_date-2023_{prefix}-98"], prefix
            )

        assert (
            f"There is more than one instance of {prefix} in "
            f"{prefix}-99_date-2023_{prefix}-98." in str(e.value)
        )

        # This test is on sub, just test twice.
        with pytest.raises(BaseException) as e:
            validation.validate_list_of_names(
                ["sub-001_ses-03_id_1232_date-123_id_1234"], "sub"
            )

    @pytest.mark.parametrize(
        "prefix_and_names",
        [
            ["sub", ["sdfsdfsd"]],
            ["sub", ["sub-1000", "sob-1001"]],
            ["sub", ["s23-999", "sub_@DATE@"]],
            ["ses", ["ses-@DATETIME@", "sub-002"]],
        ],
    )
    def test_name_does_not_begin_with_prefix(self, prefix_and_names):
        """
        Check validation that names passed to `validate_list_of_names()` start
        with the prefix prefix (sub or ses).
        """
        prefix, names = prefix_and_names
        with pytest.raises(BaseException) as e:
            validation.validate_list_of_names(names, prefix)

        assert f" do not begin with the required prefix: {prefix}" in str(
            e.value
        )

    @pytest.mark.parametrize(
        "prefix_and_names",
        [
            ["sub", ["sub- 001"]],
            ["sub", ["sub-1992_@DATE@_id 1232", "sub-1993-id_1234"]],
            ["ses", ["ses-001!", "ses-00 2"]],
            ["ses", ["ses-#001", "ses-00 2"]],
            ["ses", ["ses-001!", "ses-00%2"]],
        ],
    )
    def test_special_characters_in_format_names(self, prefix_and_names):
        """
        Check `validate_list_of_names()` catches
        spaces in passed names (not all names are bad
        """
        prefix, names = prefix_and_names
        with pytest.raises(BaseException) as e:
            validation.validate_list_of_names(names, prefix)

        assert (
            "contains characters which are not alphanumeric, dash or underscore."
            in str(e.value)
        )

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_formatting_dashes_and_underscore_alternate_incorrectly(
        self, prefix
    ):
        """
        Check `validate_list_of_names()` catches "-" and "_" that
        are not in the correct order.
        """
        # def error_message(names):

        def error_message(names):
            name_format = "name" if len(names) == 1 else "names"
            list_format = names[0] if len(names) == 1 else names
            return f"Problem with {name_format}: {list_format}."

        # Test a large range of bad names. Do not use
        # parametrize so we can use f"{prefix}".
        for test_all_names_and_bad_names in [
            [
                [f"{prefix}-001_ses-002-suffix"],
                [f"{prefix}-001_ses-002-suffix"],
            ],
            [
                [f"{prefix}-001-date_101010", f"{prefix}-002"],
                [f"{prefix}-001-date_101010"],
            ],
            [
                [
                    f"{prefix}-001",
                    f"{prefix}-002_ses-002-task-check",
                    f"{prefix}-003_date-123123",
                ],
                [f"{prefix}-002_ses-002-task-check"],
            ],
            [
                [
                    f"{prefix}-01",
                    f"{prefix}-02_ses-002-task-check",
                    f"{prefix}-03-date_101010",
                    f"{prefix}-04_ses-002-suffix",
                ],
                [
                    f"{prefix}-02_ses-002-task-check",
                    f"{prefix}-03-date_101010",
                    f"{prefix}-04_ses-002-suffix",
                ],
            ],
        ]:
            all_names, bad_names = test_all_names_and_bad_names

            with pytest.raises(BaseException) as e:
                validation.validate_list_of_names(all_names, f"{prefix}")

            assert error_message(bad_names) in str(
                e.value
            ), f"failed: {all_names}"

        # check these don't raise
        all_names = [f"{prefix}-001_hello-world_one-hundred"]
        validation.validate_list_of_names(all_names, f"{prefix}")

        all_names = [f"{prefix}-001_hello-world_suffix"]
        validation.validate_list_of_names(all_names, f"{prefix}")

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_inconsistent_value_lengths_in_list_of_names(self, prefix):
        """
        Ensure a list of sub / ses names that contain inconsistent
        leading zeros (e.g. ["sub-001", "sub-02"]) leads to an error.
        """
        for names in [
            [f"{prefix}-001", f"{prefix}-02", f"{prefix}-003"],
            [f"{prefix}-999", f"{prefix}-1000", f"{prefix}-1001"],
            [f"{prefix}-0099", f"{prefix}-100", f"{prefix}-0098"],
        ]:
            with pytest.raises(BaseException) as e:
                formatting.check_and_format_names(names, prefix)

            assert (
                f"Inconsistent value lengths for the key {prefix} were "
                f"found." in str(e.value)
            )

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_duplicate_ids_in_list_of_names(self, prefix):
        """
        Ensure a list of sub / ses names that contain duplicate sub / ses
        ids (e.g. ["sub-001", "sub-001_@DATE@"]) leads to an error.
        """
        names = [f"{prefix}-001", f"{prefix}-002", f"{prefix}-001_@DATE@"]

        with pytest.raises(BaseException) as e:
            formatting.check_and_format_names(names, prefix)

        assert (
            str(e.value) == f"{prefix} names must all have unique "
            f"integer ids after the {prefix} prefix."
        )

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_new_name_duplicates_existing(self, prefix):
        """
        Test the function `new_name_duplicates_existing()`
        that will throw an error if a sub / ses name matches
        an existing name (unless it matches exactly).
        """

        # Check an exactly matching case that should not raise and error
        new_name = f"{prefix}-002"
        existing_names = [f"{prefix}-001", f"{prefix}-002", f"{prefix}-003"]
        failed, message = validation.new_name_duplicates_existing(
            new_name, existing_names, prefix
        )

        assert not failed
        assert message == ""

        # Check a completely different case that should not raise an error.
        new_name = f"{prefix}-99999"
        existing_names = [f"{prefix}-999"]
        failed, message = validation.new_name_duplicates_existing(
            new_name, existing_names, prefix
        )

        assert not failed
        assert message == ""

        # Test a single non-exact matching case (002) that raises an error.
        new_name = f"{prefix}-002_date-12345"
        existing_names = [f"{prefix}-002_date-00000", f"{prefix}-003"]
        failed, message = validation.new_name_duplicates_existing(
            new_name, existing_names, prefix
        )

        assert failed
        assert (
            f"same {prefix} id as {prefix}-002_date-12345. "
            f"The existing folder is {prefix}-002_date-00000." in message
        )

        # Check that the exact-match case passes while the match
        # case does not.
        new_name = f"{prefix}-3"
        existing_names = [f"{prefix}-3", f"{prefix}-3_s-a"]
        failed, message = validation.new_name_duplicates_existing(
            new_name, existing_names, prefix
        )

        assert failed
        assert (
            f"A {prefix} already exists with the same {prefix} id as {prefix}-3. "
            f"The existing folder is {prefix}-3_s-a." in message
        )
