import os.path
import shutil

import pytest
from base import BaseTest

# ----------------------------------------------------------------------------------
# Inconsistent sub or ses value lengths
# ----------------------------------------------------------------------------------


class TestValidation(BaseTest):
    @pytest.mark.parametrize(
        "sub_name",
        ["sub-001", "sub-999_@DATE@", "sub-001_random-tag_another-tag"],
    )
    @pytest.mark.parametrize(
        "bad_sub_name",
        [
            "sub-3",
            "sub-04",
            "sub-0004",
            "sub-07_@DATE@",
            "sub-1321",
            "sub-22",
            "sub-234234453_@DATETIME@",
        ],
    )
    def test_warn_on_inconsistent_sub_value_lengths(
        self, project, sub_name, bad_sub_name
    ):
        """
        This test checks that inconsistent sub value lengths are properly
        detected across the project. This is performed with an assortment
        of possible filenames and leading zero conflicts.

        These conflicts are detected across the project (i.e. if you have sub-03
        in remote and sub-004 in local, a warning should be shown). Therefore
        this function tests every combination of conflict across local and central).

        Note SSH version is not tested, but the core functionality detecting
        inconsistent leading zeros is agnostic to SSH, and SSH file searching
        is tested elsewhere.
        """
        # First make conflicting leading zero subject names in the local repo
        os.makedirs(project.cfg["local_path"] / "rawdata" / sub_name)
        os.makedirs(project.cfg["local_path"] / "rawdata" / bad_sub_name)
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "sub")

        # Now, have conflicting subject names, but one in local and one in central
        new_central_path = (
            project.cfg["local_path"].parent / "central" / project.project_name
        )
        os.makedirs(new_central_path, exist_ok=True)

        project.update_config_file(central_path=new_central_path)
        os.makedirs(project.cfg["central_path"] / "rawdata" / bad_sub_name)
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / bad_sub_name)
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "sub")

        # Have conflicting subject names both in central.
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / sub_name)
        os.makedirs(project.cfg["central_path"] / "rawdata" / sub_name)
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "sub")

    @pytest.mark.parametrize(
        "ses_name",
        ["ses-01"],  # , "ses-99_@DATE@", "ses-01_random-tag_another-tag"],
    )
    @pytest.mark.parametrize(
        "bad_ses_name",
        [
            "ses-3",
            "ses-004",
            "ses-0004",
            "ses-007_@DATE@",
            "ses-1453_@DATETIME@",
            "ses-234234234",
        ],
    )
    def test_warn_on_inconsistent_ses_value_lengths__(
        self, project, ses_name, bad_ses_name
    ):
        """
        This function is exactly the same as `test_warn_on_inconsistent_sub_value_lengths()`
        but operates at the session level. This is extreme code duplication, but
        factoring the main logic out got very messy and hard to follow.
        So, in this case code duplicate is the price to pay.
        """
        # Have conflicting session names (in different subject directories)
        # on the local filesystem
        os.makedirs(
            project.cfg["local_path"] / "rawdata" / "sub-001" / ses_name
        )
        os.makedirs(
            project.cfg["local_path"] / "rawdata" / "sub-002" / bad_ses_name
        )
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "ses")

        # Now, have conflicting session names (in different subject directories)
        # where one subject directory is local and the other is central.
        new_central_path = (
            project.cfg["local_path"].parent / "central" / project.project_name
        )
        os.makedirs(new_central_path, exist_ok=True)

        project.update_config_file(central_path=new_central_path)
        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-001" / bad_ses_name
        )
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / "sub-002")
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "ses")

        # Test the case where conflicting session names are both on central.
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / "sub-001")
        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-001" / ses_name
        )
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "ses")

    def test_warn_on_inconsistent_sub_and_ses_value_lengths(self, project):
        """
        Test that warning is shown for both subject and session when
        inconsistent zeros are found in both.
        """
        os.makedirs(
            project.cfg["local_path"] / "rawdata" / "sub-001" / "ses-01"
        )
        os.makedirs(
            project.cfg["local_path"] / "rawdata" / "sub-03" / "ses-002"
        )
        self.check_inconsistent_sub_or_ses_value_length_warning(project, "sub")
        self.check_inconsistent_sub_or_ses_value_length_warning(
            project, "ses", warn_idx=1
        )

    def check_inconsistent_sub_or_ses_value_length_warning(
        self, project, prefix, warn_idx=0
    ):
        """"""
        with pytest.warns(UserWarning) as w:
            project.validate_project(error_or_warn="warn", local_only=False)

        assert (
            str(w[warn_idx].message)
            == f"Inconsistent value lengths for the key {prefix} were found. "
            f"Ensure the number of digits for the {prefix} value are the "
            f"same and prefixed with leading zeros if required."
        )

    # -----------------------------------------------------------------------------
    # Test duplicates when making folders
    # -----------------------------------------------------------------------------

    def test_duplicate_ses_or_sub_key_value_pair(self, project):
        """
        Test the check that if a duplicate key is attempt to be made
        when making a folder e.g. sub-001 exists, then make sub-001_id-123.
        After this check, make a folder that can be made (e.g. sub-003)
        just to make sure it does not raise error.

        Then, within an already made subject, try and make a session
        with a ses that already exists and check.
        """
        # Check trying to make sub only
        subs = ["sub-001_id-123", "sub-002_id-124"]
        project.make_folders(subs)

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001_id-125")

        assert (
            "A sub already "
            "exists with the same sub id as sub-001_id-125" in str(e.value)
        )

        project.make_folders("sub-003")

        # check try and make ses within a sub
        sessions = ["ses-001_date-1605", "ses-002_date-1606"]
        project.make_folders(subs, sessions)

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001_id-123", "ses-002_date-1607")

        assert (
            "A ses already exists with the same "
            "ses id as ses-002_date-1607" in str(e.value)
        )

        project.make_folders("sub-001_id-123", "ses-003")

    def test_duplicate_sub_and_ses_num_leading_zeros(self, project):
        """
        Very similar to test_duplicate_ses_or_sub_key_value_pair(),
        but explicitly check that error is raised if the same
        number is used with different number of leading zeros.
        """
        project.make_folders("sub-1")

        with pytest.raises(BaseException) as e:
            project.make_folders(
                "sub-001"
            )  # TODO: sub-1 will now catch leading zeros, which is fine.

        assert "Inconsistent value lengths for the key sub were found" in str(
            e.value
        )

        project.make_folders("sub-1", "ses-3")

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-1", "ses-003")

        assert "Inconsistent value lengths for the key ses were found" in str(
            e.value
        )

    def test_duplicate_sub_when_creating_session(self, project):
        """
        Check the unique case that a duplicate subject is
        introduced when the session is made.
        """
        project.make_folders("sub-001")

        for bad_sub_name in ["sub-001_@DATE", "sub-001_extra-key"]:
            with pytest.raises(BaseException) as e:
                project.make_folders(bad_sub_name, "ses-001")
            assert "A sub already exists" in str(e.value)

        project.make_folders("sub-001", "ses-001")

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001", "ses-001_extra-key", "behav")
        assert "A ses already exists with the same ses id as ses-001" in str(
            e.value
        )

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001_extra-key", "ses-001", "behav")
        assert "A sub already exists " in str(e.value)

        with pytest.raises(BaseException) as e:
            project.make_folders(
                "sub-001_extra-key", "ses-001_@DATE@", "behav"
            )
        assert "A sub already exists " in str(e.value)

        project.make_folders("sub-001", "ses-001", "behav")

        project.make_folders("sub-001", ["ses-001", "ses-002"])

        # Finally check that in a list of subjects, only the correct subject
        # with duplicate session is caught.
        with pytest.raises(BaseException) as e:
            project.make_folders(
                ["sub-001", "sub-002"], "ses-002_@DATE@", "ephys"
            )
        assert "A ses already exists with the same ses id as ses-002" in str(
            e.value
        )

    # -----------------------------------------------------------------------------
    # Bad unscore order
    # -----------------------------------------------------------------------------

    def test_invalid_sub_and_ses_name(self, project):
        """
        This is a slightly weird case, the name is successfully
        prefixed as 'sub-sub_100` but when the value if `sub-` is
        extracted, it is also "sub" and so an error is raised.
        """
        with pytest.raises(BaseException) as e:
            project.make_folders("sub_100")

        assert "Invalid character in subject or session value: sub" in str(
            e.value
        )

        with pytest.raises(BaseException) as e:
            project.make_folders("sub-001", "ses_100")

        assert "Invalid character in subject or session value: ses" in str(
            e.value
        )

    # -----------------------------------------------------------------------------
    # Test validation functions all
    # -----------------------------------------------------------------------------
    # these implicitly test `validate_list_of_names`.

    def test_validate_project(self, project):
        """ """
        for sub in ["sub-001", "sub-002"]:
            os.makedirs(
                project.cfg["central_path"] / "rawdata" / sub, exist_ok=True
            )

        project.make_folders(["sub-1"])

        project.validate_project(error_or_warn="error", local_only=True)

        shutil.rmtree(project.cfg["local_path"] / "rawdata")

        project.make_folders(["sub-001", "sub-002_@DATE@"])

        with pytest.raises(BaseException) as e:
            project.validate_project(error_or_warn="error", local_only=False)

        assert (
            "A sub already exists with the same sub id as sub-002_date-20231112"
            in str(e.value)
        )

        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-3", exist_ok=True
        )

        with pytest.warns(UserWarning) as w:
            project.validate_project(error_or_warn="warn", local_only=False)

        assert "Inconsistent value lengths for the key sub" in str(
            w[0].message
        )
        assert "the same sub id as sub-002_date-20231112." in str(w[1].message)
        assert "with the same sub id as sub-002" in str(w[2].message)

        project.make_folders("sub-001", ["ses-0001_@DATE@", "ses-0002"])
        os.makedirs(
            project.cfg["central_path"]
            / "rawdata"
            / "sub-004"
            / "ses-01_@DATE@",
            exist_ok=True,
        )  # TODO: fix path length

        with pytest.warns(UserWarning) as w:
            project.validate_project(error_or_warn="warn", local_only=False)

        assert "Inconsistent value lengths for the key ses were found." in str(
            w[3].message
        )

    # 1) test_new_name_duplicates_existing
    # 2) document everything
    # 3) fix passing around 'verbose' argument.
    # 3) final refactor
    # 4) Make data transfer keywords more intuitive.
    # 5) release on conda?
    # 6) ping on 'allow rclone at any time of day'
