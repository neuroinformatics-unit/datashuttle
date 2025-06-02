import os.path
import shutil

import pytest
from base import BaseTest

from datashuttle import quick_validate_project
from datashuttle.utils import formatting, validation
from datashuttle.utils.custom_exceptions import NeuroBlueprintError

# -----------------------------------------------------------------------------
# Inconsistent sub or ses value lengths
# -----------------------------------------------------------------------------


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

        These conflicts are detected across the project (i.e. if you have
        sub-03 in remote and sub-004 in local, a warning should be shown).
        Therefore this function tests every combination of conflict across
        local and central).

        Note SSH version is not tested, but the core functionality detecting
        inconsistent leading zeros is agnostic to SSH, and SSH file searching
        is tested elsewhere.
        """
        # First make conflicting leading zero subject names in the local repo
        sub_name = formatting.format_names([sub_name], "sub")[0]
        bad_sub_name = formatting.format_names([bad_sub_name], "sub")[0]

        os.makedirs(project.cfg["local_path"] / "rawdata" / sub_name)
        os.makedirs(project.cfg["local_path"] / "rawdata" / bad_sub_name)

        self.check_inconsistent_sub_or_ses_value_length_warning(
            project, include_central=False
        )

        # Now, have conflicting subject names,
        # but one in local and one in central
        new_central_path = (
            project.cfg["local_path"].parent / "central" / project.project_name
        )
        os.makedirs(new_central_path, exist_ok=True)

        project.update_config_file(central_path=new_central_path)
        os.makedirs(project.cfg["central_path"] / "rawdata" / bad_sub_name)
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / bad_sub_name)
        self.check_inconsistent_sub_or_ses_value_length_warning(project)

        # Have conflicting subject names both in central.
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / sub_name)
        os.makedirs(project.cfg["central_path"] / "rawdata" / sub_name)
        self.check_inconsistent_sub_or_ses_value_length_warning(project)

    @pytest.mark.parametrize(
        "ses_name",
        ["ses-01", "ses-99_@DATE@", "ses-01_random-tag_another-tag"],
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
    def test_warn_on_inconsistent_ses_value_lengths(
        self, project, ses_name, bad_ses_name
    ):
        """
        This function is exactly the same as
        `test_warn_on_inconsistent_sub_value_lengths()` but operates at the
        session level. This is extreme code duplication, but
        factoring the main logic out got very messy and hard to follow.
        """
        ses_name = formatting.format_names([ses_name], "ses")[0]
        bad_ses_name = formatting.format_names([bad_ses_name], "ses")[0]

        # Have conflicting session names (in different subject directories)
        # on the local filesystem
        os.makedirs(
            project.cfg["local_path"] / "rawdata" / "sub-001" / ses_name
        )
        os.makedirs(
            project.cfg["local_path"] / "rawdata" / "sub-002" / bad_ses_name
        )
        self.check_inconsistent_sub_or_ses_value_length_warning(
            project, include_central=False
        )

        # Now, have conflicting session names (in different subject
        # directories) where one subject directory is local and the
        # other is central.
        new_central_path = (
            project.cfg["local_path"].parent / "central" / project.project_name
        )
        os.makedirs(new_central_path, exist_ok=True)

        project.update_config_file(central_path=new_central_path)
        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-001" / bad_ses_name
        )
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / "sub-002")
        self.check_inconsistent_sub_or_ses_value_length_warning(project)

        # Test the case where conflicting session names are both on central.
        shutil.rmtree(project.cfg["local_path"] / "rawdata" / "sub-001")
        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-001" / ses_name
        )
        self.check_inconsistent_sub_or_ses_value_length_warning(project)

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
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
        self.check_inconsistent_sub_or_ses_value_length_warning(
            project, include_central=False
        )
        self.check_inconsistent_sub_or_ses_value_length_warning(
            project, warn_idx=1, include_central=False
        )

    def check_inconsistent_sub_or_ses_value_length_warning(
        self, project, warn_idx=0, include_central=True
    ):
        """"""
        with pytest.warns(UserWarning) as w:
            project.validate_project(
                "rawdata", display_mode="warn", include_central=include_central
            )

        assert "VALUE_LENGTH" in str(w[warn_idx].message)

    # -------------------------------------------------------------------------
    # Test duplicates when making folders
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
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
        project.create_folders("rawdata", subs)

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders("rawdata", "sub-001_id-125")

        assert "DUPLICATE_NAME" in str(e.value)

        project.create_folders("rawdata", "sub-003")

        # check try and make ses within a sub
        sessions = ["ses-001_date-20241105", "ses-002_date-20241106"]
        project.create_folders("rawdata", subs, sessions)

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders(
                "rawdata", "sub-001_id-123", "ses-002_date-20241107"
            )
        assert "DUPLICATE_NAME" in str(e.value)

        project.create_folders("rawdata", "sub-001_id-123", "ses-003")

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
    def test_duplicate_sub_and_ses_num_leading_zeros(self, project):
        """
        Very similar to test_duplicate_ses_or_sub_key_value_pair(),
        but explicitly check that error is raised if the same
        number is used with different number of leading zeros.
        """
        project.create_folders("rawdata", "sub-1")

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders("rawdata", "sub-001")

        assert "VALUE_LENGTH" in str(e.value)

        project.create_folders("rawdata", "sub-1", "ses-3")

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders("rawdata", "sub-1", "ses-003")

        assert "DUPLICATE_NAME" in str(e.value)

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
    def test_duplicate_sub_when_creating_session(self, project):
        """
        Check the unique case that a duplicate subject is
        introduced when the session is made.
        """
        project.create_folders("rawdata", "sub-001")

        for bad_sub_name in ["sub-001_@DATE@", "sub-001_extra-key"]:
            with pytest.raises(NeuroBlueprintError) as e:
                project.create_folders("rawdata", bad_sub_name, "ses-001")

            assert "DUPLICATE_NAME" in str(e.value)

        project.create_folders("rawdata", "sub-001", "ses-001")

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders(
                "rawdata", "sub-001", "ses-001_extra-key", "behav"
            )
        assert "DUPLICATE_NAME" in str(e.value)

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders(
                "rawdata", "sub-001_extra-key", "ses-001", "behav"
            )
        assert "DUPLICATE_NAME" in str(e.value)

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders(
                "rawdata", "sub-001_extra-key", "ses-001_@DATE@", "behav"
            )
        assert "DUPLICATE_NAME" in str(e.value)

        project.create_folders("rawdata", "sub-001", "ses-001", "behav")

        project.create_folders("rawdata", "sub-001", ["ses-001", "ses-002"])

        # Finally check that in a list of subjects, only the correct subject
        # with duplicate session is caught.
        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders(
                "rawdata", ["sub-001", "sub-002"], "ses-002_@DATE@", "ephys"
            )
        assert "DUPLICATE_NAME" in str(e.value)

    def test_duplicate_ses_across_subjects(self, project):
        """
        Quick test that duplicate session folders only raise
        an error when they are in the same subject.
        """
        project.create_folders("rawdata", "sub-001", "ses-001")
        project.create_folders("rawdata", "sub-002", "ses-001_@DATE@")

        project.validate_project(
            "rawdata", display_mode="error", include_central=False
        )

        with pytest.raises(NeuroBlueprintError):
            project.create_folders("rawdata", "sub-001", "ses-001_@DATE@")

    # -------------------------------------------------------------------------
    # Bad underscore order
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
    def test_invalid_sub_and_ses_name(self, project):
        """
        This is a slightly weird case, the name is successfully
        prefixed as 'sub-sub_100` but when the value if `sub-` is
        extracted, it is also "sub" and so an error is raised.
        """
        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders("rawdata", "sub_100")

        assert (
            "BAD_VALUE: The value for prefix sub in name sub-sub_100 is not an integer."
            == str(e.value)
        )

        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders("rawdata", "sub-001", "ses_100")

        assert (
            "BAD_VALUE: The value for prefix ses in name ses-ses_100 is not an integer."
            == str(e.value)
        )

    # -------------------------------------------------------------------------
    # Test validate project
    # -------------------------------------------------------------------------

    def test_validate_project(self, project):
        """
        Test the `validate_project` function over all it's arguments.
        Note not every validation case is tested exhaustively, these
        are tested in `test_validation_unit.py` elsewhere here.
        """
        for sub in ["sub-001", "sub-002"]:
            os.makedirs(
                project.cfg["central_path"] / "rawdata" / sub, exist_ok=True
            )

        project.create_folders("rawdata", ["sub-002_id-11"])

        # The bad sub name is not caught when testing locally only.
        project.validate_project(
            "rawdata", display_mode="error", include_central=False
        )

        project.create_folders("rawdata", "sub-001")

        # Now the bad sub is caught as we check against central also.
        with pytest.raises(NeuroBlueprintError) as e:
            project.validate_project(
                "rawdata", display_mode="error", include_central=True
            )
        assert "DUPLICATE_NAME" in str(e.value)
        assert "Path" in str(e.value)  # cursory check Path is returned

        # Now check warnings are shown when there are multiple validation
        # issues across local and central.
        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-3", exist_ok=True
        )

        with pytest.warns(UserWarning) as w:
            project.validate_project(
                "rawdata", display_mode="warn", include_central=True
            )
        assert "DUPLICATE_NAME" in str(w[0].message)
        assert "DUPLICATE_NAME" in str(w[1].message)
        assert "VALUE_LENGTH" in str(w[2].message)

        # Finally, check that some bad sessions (ses-01) are caught.
        project.create_folders(
            "rawdata", "sub-001", ["ses-0001_id-11", "ses-0002"]
        )
        os.makedirs(
            project.cfg["central_path"]
            / "rawdata"
            / "sub-004"
            / "ses-01_id-11",
            exist_ok=True,
        )

        with pytest.warns(UserWarning) as w:
            project.validate_project(
                "rawdata", display_mode="warn", include_central=True
            )
        assert (
            "VALUE_LENGTH: Inconsistent value lengths for the prefix: sub"
            in str(w[2].message)
        )
        assert (
            "VALUE_LENGTH: Inconsistent value lengths for the prefix: ses"
            in str(w[3].message)
        )
        assert "Path" not in str(
            w[3].message
        )  # no path in VALUE_LENGTH errors

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_validate_project_returned_list(self, project, prefix):
        """ """
        bad_names = [
            f"{prefix}-001",
            f"{prefix}-001_@DATE@",
            f"{prefix}_002_id_1",
            f"{prefix}-02",
            f"{prefix}-002_date-1",
        ]

        if prefix == "sub":
            project.create_folders(
                "rawdata", bad_names, bypass_validation=True
            )
        else:
            project.create_folders(
                "rawdata", "sub-001", bad_names, bypass_validation=True
            )

        error_messages = project.validate_project(
            "rawdata", "warn", include_central=False
        )
        concat_error = "".join(error_messages)

        assert "DATETIME" in concat_error
        assert "BAD_VALUE" in concat_error
        assert "DUPLICATE_NAME" in concat_error
        assert "VALUE_LENGTH" in concat_error

    def test_output_paths_are_valid(self, project):
        """ """
        sub_name = "sub-001x"
        ses_name = "ses-001x"
        project.create_folders(
            "rawdata", sub_name, ses_name, bypass_validation=True
        )

        error_messages = project.validate_project(
            "rawdata", "warn", include_central=False
        )

        sub_path = error_messages[0].split("Path: ")[-1]
        ses_path = error_messages[1].split("Path: ")[-1]

        assert (
            sub_path
            == (project.cfg["local_path"] / "rawdata" / sub_name).as_posix()
        )
        assert (
            ses_path
            == (
                project.cfg["local_path"] / "rawdata" / sub_name / ses_name
            ).as_posix()
        )

    # -------------------------------------------------------------------------
    # Test validate names against project
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
    def test_validate_names_against_project_with_bad_existing_names(
        self, project
    ):
        """
        When using `validate_names_against_project()` there are
        three possible classes of error:
        1) error in the passed names.
        2) an error already exists in the project.
        3) an error in the 'interaction' between names and project (e.g.
           all names are okay, all project names are okay, but new names duplicate
           an existing name).

        `validate_names_against_project()` is only interested in catching 1) and 2)
        but not reporting errors for names that already exist in the project.

        This checks that the validation of names is not affected by existing
        bad names in the project. The only case where this matters is if
        within the project, the subject or session value length is inconsistent.
        Then we don't know what to validate the names against and an
        error indicating this specific problem is raised.
        """
        # Make some bad project names. We will check these don't interfere
        # with the validation of the passed names.
        project.create_folders(
            "rawdata", "sub-abc", "ses-abc", bypass_validation=True
        )

        # Check the bad names do not interference with an example
        # bad validation within the names list.
        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg, "rawdata", ["sab-001"], include_central=False
            )
        assert (
            "MISSING_PREFIX: The prefix sub was not found in the name: sab-001"
            in str(e.value)
        )

        # Now check the bad names don't interfere with
        # inconsistent value lengths or duplicate names.
        project.create_folders("rawdata", "sub-004", "ses-001")

        # Inconsistent value lengths
        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg, "rawdata", ["sub-0002"], include_central=False
            )
        assert (
            "VALUE_LENGTH: Inconsistent value lengths for the prefix: sub"
            in str(e.value)
        )

        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                ["sub-004"],
                ["ses-0002"],
                include_central=False,
            )
        assert (
            "VALUE_LENGTH: Inconsistent value lengths for the prefix: ses"
            in str(e.value)
        )

        # Duplicate names
        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                ["sub-004_id-123"],
                include_central=False,
            )
        assert (
            "DUPLICATE_NAME: The prefix for sub-004_id-123 duplicates the name: sub-004"
            in str(e.value)
        )

        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                ["sub-004"],
                ["ses-001_date-121212"],
                include_central=False,
            )
        assert (
            "DUPLICATE_NAME: The prefix for ses-001_date-121212 duplicates the name: ses-001"
            in str(e.value)
        )
        assert "Path" in str(e.value)  # quick check Path is included

        # Finally make folders within the existing project that have
        # inconsistent value lengths, and check the correct error is raised.

        # First for session
        project.create_folders(
            "rawdata",
            ["sub-001"],
            ["ses-01", "ses-002"],
            bypass_validation=True,
        )

        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                ["sub-001"],
                ["ses-03"],
                include_central=False,
            )
        assert (
            "Cannot check names for inconsistent value lengths because the session value"
            in str(e.value)
        )

        # Then subject
        project.create_folders("rawdata", ["sub-02"], bypass_validation=True)
        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                ["sub-003"],
                include_central=False,
                display_mode="error",
            )

        assert (
            "Cannot check names for inconsistent value lengths because the subject value"
            in str(e.value)
        )

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
    def test_validate_names_against_project_interactions(self, project):
        """
        Check that interactions between the list of names and existing
        project are caught. This includes duplicate subject / session
        names as well as inconsistent subject / session value lengths.
        """
        project.create_folders(
            "rawdata", ["sub-1_id-abc", "sub-2_id-b", "sub-3_id-c"]
        )

        # Check an exact match passes
        sub_names = ["sub-1_id-abc"]
        validation.validate_names_against_project(
            project.cfg,
            "rawdata",
            sub_names,
            include_central=False,
            display_mode="error",
        )

        # Now check a clashing subject (sub-1) throws an error
        sub_names = ["sub-2_id-b", "sub-1_id-11", "sub-3_id-c"]

        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                sub_names,
                include_central=False,
                display_mode="error",
            )
        assert "DUPLICATE_NAME" in str(e.value)

        # Now check multiple different types of error are warned about
        sub_names = ["sub-002", "sub-1_id-11", "sub-3_id-c", "sub-4"]

        with pytest.warns(UserWarning) as w:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                sub_names,
                include_central=False,
                display_mode="warn",
            )
        # this warning arises from inconsistent value lengths within the
        # passed sub_names
        assert "VALUE_LENGTH" in str(w[0].message)
        # This warning arises from inconstant value lengths between
        # sub_names and the rest of the project. This behaviour could be optimisHed.
        assert "VALUE_LENGTH" in str(w[1].message)
        assert "DUPLICATE_NAME" in str(w[2].message)
        assert "DUPLICATE_NAME" in str(w[3].message)

        if project.is_local_project():
            return

        # Now make some new paths on central. Pass a bad new subject name
        # (sub-4) and check no error is raised when local_only is `True`
        # but the error is discovered when `False`.
        os.makedirs(
            project.cfg["central_path"] / "rawdata" / "sub-4_date-20231215"
        )

        sub_names = ["sub-4", "sub-5"]
        validation.validate_names_against_project(
            project.cfg,
            "rawdata",
            sub_names,
            include_central=False,
            display_mode="error",
        )

        with pytest.raises(NeuroBlueprintError) as e:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                sub_names,
                include_central=True,
                display_mode="error",
            )
        assert "DUPLICATE_NAME" in str(e.value)

        # Now, make some sessions locally and on central. Check that
        # the correct errors are warned when we check at the subject level.
        # Now that session checks are performed per-subject.
        os.makedirs(
            project.cfg["central_path"]
            / "rawdata"
            / "sub-4_date-20231215"
            / "ses-003"
        )
        project.create_folders("rawdata", "sub-2_id-b", ["ses-001", "ses-002"])

        # Check no error is raised for exact match.
        sub_names = ["sub-1_id-abc", "sub-2_id-b", "sub-4_date-20231215"]
        ses_names = ["ses-001", "ses-002"]

        validation.validate_names_against_project(
            project.cfg,
            "rawdata",
            sub_names,
            ses_names,
            include_central=True,
            display_mode="error",
        )

        # ses-002 is bad for sub-2, ses-003 is bad for sub-4
        sub_names = ["sub-1_id-abc", "sub-2_id-b", "sub-4_date-20231215"]
        ses_names = ["ses-002_id-11", "ses-003_id-random"]

        with pytest.warns(UserWarning) as w:
            validation.validate_names_against_project(
                project.cfg,
                "rawdata",
                sub_names,
                ses_names,
                include_central=True,
                display_mode="warn",
            )
        assert "DUPLICATE_NAME" in str(w[0].message)
        assert "DUPLICATE_NAME" in str(w[1].message)

    @pytest.mark.parametrize("project", ["local", "full"], indirect=True)
    def test_tags_in_name_templates_pass_validation(self, project):
        """
        It is useful to allow tags in the `name_templates` as it means
        auto-completion in the TUI can use tags for automatic name
        generation. Because all subject and session names are
        fully formatted (e.g. @DATE@ converted to actual dates)
        prior to validation, the regexp must also have @DATE@
        and other tags with their regexp equivalent. Check
        this behaviour here.
        """
        name_templates = {
            "on": True,
            "sub": "sub-\d\d_@DATE@",
            "ses": "ses-\d\d\d@DATETIME@",
        }

        project.set_name_templates(name_templates)

        # Standard behaviour, should not raise
        project.create_folders(
            "rawdata",
            "sub-01_date-20240101",
            "ses-001_datetime-20240101T142323",
        )
        # added tags, should not raise
        project.create_folders("rawdata", "sub-02@DATE@", "ses-001_@DATETIME@")

        # break the name template validation, for sub, should raise
        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders("rawdata", "sub-03_datex-202401")
        assert "TEMPLATE: The name: sub-03_datex-202401" in str(e.value)

        # break the name template validation, for ses, should raise
        with pytest.raises(NeuroBlueprintError) as e:
            project.create_folders(
                "rawdata", "sub-03_date-20240101", "ses-001_datex-20241212"
            )
        assert "TEMPLATE: The name: ses-001_datex-20241212" in str(e.value)

        # Do a quick test for time
        name_templates["sub"] = "sub-\d\d_@TIME@"
        project.set_name_templates(name_templates)

        # use time tag, should not raise
        project.create_folders(
            "rawdata",
            "sub-03@TIME@",
        )

        # use misspelled time tag, should raise
        with pytest.raises(NeuroBlueprintError):
            project.create_folders("rawdata", "sub-03_mime_010101")
        assert "TEMPLATE: The name: ses-001_datex-20241212" in str(e.value)

    def test_name_templates_validate_project(self, project):
        """
        TODO
        """
        name_templates = {
            "on": True,
            "sub": "sub-\d\d_id-\d.?",
            "ses": "ses-\d\d_id-\d.?",
        }
        project.set_name_templates(name_templates)

        project.create_folders(
            "rawdata", "sub-01_id-2b", "ses-01_id-1a", bypass_validation=True
        )

        project.validate_project("rawdata", "error", include_central=False)

        project.create_folders(
            "rawdata", "sub-02_id-a1", "ses-02_id-aa", bypass_validation=True
        )

        with pytest.warns(UserWarning) as w:
            project.validate_project("rawdata", "warn", include_central=False)

        assert (
            "TEMPLATE: The name: sub-02_id-a1 does not match the template: sub-\\d\\d_id-\\d.?"
            in str(w[0].message)
        )
        assert (
            "TEMPLATE: The name: ses-02_id-aa does not match the template: ses-\\d\\d_id-\\d.?"
            in str(w[1].message)
        )

    # ----------------------------------------------------------------------------------
    # Test Quick Validation Function
    # ----------------------------------------------------------------------------------

    def test_quick_validation(self, mocker, project):
        """ """
        project.create_folders("rawdata", "sub-1")
        os.makedirs(project.cfg["local_path"] / "rawdata" / "sub-02")
        project.create_folders("derivatives", "sub-1")
        os.makedirs(project.cfg["local_path"] / "derivatives" / "sub-02")

        with pytest.warns(UserWarning) as w:
            quick_validate_project(
                project.get_local_path(),
                display_mode="warn",
                top_level_folder=None,
            )
        assert "VALUE_LENGTH" in str(w[0].message)
        assert "VALUE_LENGTH" in str(w[1].message)
        assert len(w) == 2

        # For good measure, monkeypatch and change all defaults,
        # ensuring they are propagated to the validate_project
        # function (which is tested above)
        import datashuttle

        spy_validate_func = mocker.spy(
            datashuttle.datashuttle_functions.validation, "validate_project"
        )

        quick_validate_project(
            project.get_local_path(),
            display_mode="print",
            top_level_folder="derivatives",
            name_templates={"on": False},
        )

        _, kwargs = spy_validate_func.call_args_list[0]
        assert kwargs["display_mode"] == "print"
        assert kwargs["top_level_folder_list"] == ["derivatives"]
        assert kwargs["name_templates"] == {"on": False}

    def test_quick_validation_top_level_folder(self, project):
        """
        Test that errors are raised as expected on
        bad project path input.
        """
        with pytest.raises(FileNotFoundError) as e:
            quick_validate_project(
                project.get_local_path() / "does not exist",
                display_mode="error",
            )
        assert (
            "Cannot perform validation. No file or folder found at `project_path`:"
            in str(e.value)
        )

    # ----------------------------------------------------------------------------------
    # Test Strict Validation and High-Level Checks
    # ----------------------------------------------------------------------------------

    @pytest.mark.parametrize("top_level_folder", ["rawdata", "derivatives"])
    def test_strict_mode_validation(self, project, top_level_folder):
        """ """
        project.create_folders(
            top_level_folder,
            ["sub-001", "sub-002"],
            ["ses-001", "ses-002"],
            ["ephys", "behav"],
        )

        project.validate_project(
            top_level_folder, "error", include_central=False, strict_mode=True
        )

        os.makedirs(
            project.cfg["local_path"] / top_level_folder / "bad_sub_name"
        )
        os.makedirs(
            project.cfg["local_path"]
            / top_level_folder
            / "sub-001"
            / "bad_sesname"
        )

        os.makedirs(
            project.cfg["local_path"]
            / top_level_folder
            / "sub-002"
            / "ses-002"
            / "bad_datatype_name"
        )

        with pytest.warns(UserWarning) as w:
            project.validate_project(
                top_level_folder,
                "warn",
                include_central=False,
                strict_mode=True,
            )

        assert (
            "BAD_NAME: The name: bad_sub_name of type: sub is not valid"
            in str(w[0].message)
        )
        assert (
            "BAD_NAME: The name: bad_sesname of type: ses is not valid."
            in str(w[1].message)
        )
        assert (
            "DATATYPE: bad_datatype_name is not a valid datatype name."
            in str(w[2].message)
        )
        assert len(w) == 3

        with pytest.raises(ValueError) as e:
            project.validate_project(
                top_level_folder,
                "warn",
                include_central=True,
                strict_mode=True,
            )

        assert (
            "`strict_mode` is currently only available for `include_central=False`."
            in str(e.value)
        )

    @pytest.mark.parametrize("top_level_folder", ["rawdata", "derivatives"])
    def test_check_high_level_project_structure(
        self, project, top_level_folder
    ):
        """
        Check that local and central project names are properly formatted
        and that
        """
        with pytest.warns(UserWarning) as w:
            project.validate_project(
                top_level_folder, "warn", include_central=True
            )

        assert len(w) == 2
        assert "TOP_LEVEL_FOLDER: The local project" in str(w[0].message)
        assert "TOP_LEVEL_FOLDER: The central project" in str(w[1].message)

        project.create_folders("rawdata", "sub-001")
        with pytest.warns(UserWarning) as w:
            project.validate_project(
                top_level_folder, "warn", include_central=True
            )

        assert len(w) == 1
        assert "TOP_LEVEL_FOLDER: The central project" in str(w[0].message)

        # Should be fine now that both folders have rawdata or derivatives
        os.makedirs(project.get_central_path() / "derivatives")
        project.validate_project(
            top_level_folder, "error", include_central=True
        )

        # Make a bad project name and check its caught
        project.cfg["local_path"] = (
            project.cfg["local_path"].parent / "bad@project@name@"
        )
        project.cfg["central_path"] = (
            project.cfg["central_path"].parent / "bad@project@name@"
        )

        (project.cfg["local_path"] / "rawdata").mkdir(parents=True)
        (project.cfg["central_path"] / "rawdata").mkdir(parents=True)

        with pytest.warns(UserWarning) as w:
            project.validate_project("rawdata", "warn", include_central=True)

        assert len(w) == 2
        assert (
            "PROJECT_NAME: The local project name folder bad@project@name@"
            in str(w[0].message)
        )
        assert (
            "PROJECT_NAME: The central project name folder bad@project@name@"
            in str(w[1].message)
        )
