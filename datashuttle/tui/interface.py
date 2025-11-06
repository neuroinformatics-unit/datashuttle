from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import subprocess

    import paramiko

    from datashuttle.configs.config_class import Configs
    from datashuttle.utils.custom_types import InterfaceOutput, TopLevelFolder

from datashuttle import DataShuttle
from datashuttle.configs import load_configs
from datashuttle.utils import aws, gdrive, rclone, ssh, utils


class Interface:
    """An interface class between the TUI and datashuttle API.

    Takes input to all datashuttle functions as passed from the TUI,
    outputs success status (True or False) and optional data, in the
    case of False.

    `self.project` is initialised when project is loaded.

    Interface functions typically return an `InterfaceOutput` type
    is contains a boolean in the first entry and output in the second
    entry. The first entry is True if the API call ran successfully
    and False if it threw an error. The output will contain any
    relevant data if successful, otherwise it will contain an error message.
    """

    def __init__(self) -> None:
        """Initialise the Interface class."""
        self.project: DataShuttle
        self.validation_templates: Dict = {}
        self.tui_settings: Dict = {}

        self.gdrive_rclone_setup_process: subprocess.Popen | None = None
        self.gdrive_setup_process_killed: bool = False

    def select_existing_project(self, project_name: str) -> InterfaceOutput:
        """Load an existing project into `self.project`.

        Parameters
        ----------
        project_name
            The name of the datashuttle project to load.
            Must already exist.

        """
        try:
            project = DataShuttle(project_name, print_startup_message=False)
            self.project = project
            return True, None

        except BaseException as e:
            return False, str(e)

    def setup_new_project(
        self, project_name: str, cfg_kwargs: Dict
    ) -> InterfaceOutput:
        """Set up a new project and load into `self.project`.

        Parameters
        ----------
        project_name
            Name of the project to set up.

        cfg_kwargs
            The configurations to set the new project to.

        """
        try:
            project = DataShuttle(project_name, print_startup_message=False)

            project.make_config_file(**cfg_kwargs)

            self.project = project

            return True, None

        except BaseException as e:
            return False, str(e)

    def set_configs_on_existing_project(
        self, cfg_kwargs: Dict
    ) -> InterfaceOutput:
        """Update the settings on an existing project.

        Only the settings passed in `cfg_kwargs` are updated.

        Parameters
        ----------
        cfg_kwargs
            The configs and new values to update.

        """
        try:
            self.project.update_config_file(**cfg_kwargs)
            return True, None

        except BaseException as e:
            return False, str(e)

    def create_folders(
        self,
        sub_names: List[str],
        ses_names: Optional[List[str]],
        datatype: List[str],
    ) -> InterfaceOutput:
        """Create folders through datashuttle.

        Parameters
        ----------
        sub_names
            A list of un-formatted / unvalidated subject names to create.

        ses_names
            A list of un-formatted / unvalidated session names to create.

        datatype
            A list of canonical datatype names to create.

        """
        top_level_folder = self.tui_settings["top_level_folder_select"][
            "create_tab"
        ]
        bypass_validation = self.tui_settings["bypass_validation"]

        allow_letters_in_sub_ses_values = self.tui_settings[
            "allow_letters_in_sub_ses_values"
        ]

        try:
            self.project.create_folders(
                top_level_folder,
                sub_names=sub_names,
                ses_names=ses_names,
                datatype=datatype,
                bypass_validation=bypass_validation,
                allow_letters_in_sub_ses_values=allow_letters_in_sub_ses_values,
            )
            return True, None

        except BaseException as e:
            return False, str(e)

    def validate_names(
        self,
        sub_names: List[str],
        ses_names: Optional[List[str]],
    ) -> InterfaceOutput:
        """Validate a list of subject / session names.

        This is used to populate the Input tooltips with validation errors.
        Uses a central `_format_and_validate_names()` that is also
        called during folder creation itself, to ensure these a
        results always match.

        Parameters
        ----------
        sub_names
            List of subject names to format.

        ses_names
            List of session names to format.

        """
        top_level_folder = self.tui_settings["top_level_folder_select"][
            "create_tab"
        ]

        allow_letters_in_sub_ses_values = self.tui_settings[
            "allow_letters_in_sub_ses_values"
        ]

        try:
            format_sub, format_ses = self.project._format_and_validate_names(
                top_level_folder,
                sub_names,
                ses_names,
                self.get_validation_templates(),
                bypass_validation=False,
                allow_letters_in_sub_ses_values=allow_letters_in_sub_ses_values,
            )

            return True, {
                "format_sub": format_sub,
                "format_ses": format_ses,
            }

        except BaseException as e:
            return False, str(e)

    def validate_project(
        self,
        top_level_folder: list[str] | None,
        include_central: bool,
        strict_mode: bool,
        allow_letters_in_sub_ses_values: bool,
    ) -> tuple[bool, list[str] | str]:
        """Wrap the validate project function.

        This returns a list of validation errors (empty if there are none).

        Parameters
        ----------
        top_level_folder
            The "rawdata" or "derivatives" folder to validate. If `None`, both
            will be validated.
        include_central
            If `True`, the central project is also validated.
        strict_mode
            If `True`, validation will be run in strict mode.
        allow_letters_in_sub_ses_values
            If `True`, alphanumeric values will not raise an error.

        Returns
        -------
        success
            A bool inicating whether the validation was run successfully

        issues
            A message or list of discovered validation issues.

        """
        try:
            results = self.project.validate_project(
                top_level_folder=top_level_folder,
                display_mode="print",  # unused
                include_central=include_central,
                strict_mode=strict_mode,
                allow_letters_in_sub_ses_values=allow_letters_in_sub_ses_values,
            )
            return True, results

        except BaseException as e:
            return False, str(e)

    # Transfer
    # ----------------------------------------------------------------------------------

    def transfer_entire_project(self, upload: bool) -> InterfaceOutput:
        """Transfer the entire project (all canonical top-level folders).

        Parameters
        ----------
        upload
            Upload from local to central if `True`, otherwise download
            from central to remote.

        """
        try:
            if upload:
                transfer_func = self.project.upload_entire_project
            else:
                transfer_func = self.project.download_entire_project

            transfer_func(
                overwrite_existing_files=self.tui_settings[
                    "overwrite_existing_files"
                ],
                dry_run=self.tui_settings["dry_run"],
            )

            return True, None

        except BaseException as e:
            return False, str(e)

    def transfer_top_level_only(
        self, selected_top_level_folder: str, upload: bool
    ) -> InterfaceOutput:
        """Transfer all files within a selected top level folder.

        Parameters
        ----------
        selected_top_level_folder
            The top level folder selected in the TUI for this transfer window.

        upload
            Upload from local to central if `True`, otherwise download
            from central to remote.

        """
        assert selected_top_level_folder in ["rawdata", "derivatives"]

        try:
            if selected_top_level_folder == "rawdata":
                transfer_func = (
                    self.project.upload_rawdata
                    if upload
                    else self.project.download_rawdata
                )
            elif selected_top_level_folder == "derivatives":
                transfer_func = (
                    self.project.upload_derivatives
                    if upload
                    else self.project.download_derivatives
                )

            transfer_func(
                overwrite_existing_files=self.tui_settings[
                    "overwrite_existing_files"
                ],
                dry_run=self.tui_settings["dry_run"],
            )

            return True, None

        except BaseException as e:
            return False, str(e)

    def transfer_custom_selection(
        self,
        selected_top_level_folder: TopLevelFolder,
        sub_names: List[str],
        ses_names: List[str],
        datatype: List[str],
        upload: bool,
    ) -> InterfaceOutput:
        """Transfer a custom selection of subjects / sessions / datatypes.

        Parameters
        ----------
        selected_top_level_folder
            The top level folder selected in the TUI for this transfer window.

        sub_names
            Subject names or subject-level canonical transfer keys to transfer.

        ses_names
            Session names or session-level canonical transfer keys to transfer.

        datatype
            Datatypes or datatype-level canonical transfer keys to transfer.

        upload
            Upload from local to central if `True`, otherwise download
            from central to remote.

        """
        try:
            if upload:
                transfer_func = self.project.upload_custom
            else:
                transfer_func = self.project.download_custom

            transfer_func(
                selected_top_level_folder,
                sub_names=sub_names,
                ses_names=ses_names,
                datatype=datatype,
                overwrite_existing_files=self.tui_settings[
                    "overwrite_existing_files"
                ],
                dry_run=self.tui_settings["dry_run"],
            )

            return True, None

        except BaseException as e:
            return False, str(e)

    # Name templates
    # ----------------------------------------------------------------------------------

    def get_validation_templates(self) -> Dict:
        """Return the `validation_templates` defining templates to validate against.

        These are stored in a variable to avoid constantly
        reading these values from disk where they are stored in
        `persistent_settings`. It is critical this variable
        and the file contents are in sync, so when changed
        on the TUI side they are updated also, in `get_tui_settings`.
        """
        if not self.validation_templates:
            self.validation_templates = self.project.get_validation_templates()

        return self.validation_templates

    def set_validation_templates(
        self, validation_templates: Dict
    ) -> InterfaceOutput:
        """Set the `validation_templates` here and on disk.

        See `get_validation_templates` for more information.
        """
        try:
            self.project.set_validation_templates(validation_templates)
            self.validation_templates = validation_templates
            return True, None

        except BaseException as e:
            return False, str(e)

    def get_tui_settings(self) -> Dict:
        """Return the "tui" field of `persistent_settings`.

        Similar to `get_validation_templates`, there are held on the
        class to avoid constantly reading from disk.
        """
        if not self.tui_settings:
            self.tui_settings = self.project._load_persistent_settings()["tui"]

        return self.tui_settings

    def save_tui_settings(
        self, value: Any, key: str, key_2: Optional[str] = None
    ) -> None:
        """Update the "tui" field of the `persistent_settings` on disk.

        Parameters
        ----------
        value
            Value to set the `persistent_settings` tui field to

        key
            First key of the tui `persistent_settings` to update
            e.g. "top_level_folder_select"

        key_2
            Optionals second level of the dictionary to update.
            e.g. "create_tab"

        """
        if key_2 is None:
            self.tui_settings[key] = value
        else:
            self.tui_settings[key][key_2] = value

        self.project._update_persistent_setting("tui", self.tui_settings)

    # Setup SSH
    # ----------------------------------------------------------------------------------

    def get_central_host_id(self) -> str:
        """Return the central host id for ssh."""
        return self.project.cfg["central_host_id"]

    def get_configs(self) -> Configs:
        """Return Datashuttle Configs."""
        return self.project.cfg

    def get_textual_compatible_project_configs(self) -> Configs:
        """Return Datashuttle configs with paths stored as str.

        In some cases textual requires str representation. This method
        returns datashuttle configs with all paths that are Path
        converted to str.
        """
        cfg_to_load = copy.deepcopy(self.project.cfg)
        load_configs.convert_str_and_pathlib_paths(cfg_to_load, "path_to_str")
        return cfg_to_load

    def get_next_sub(
        self, top_level_folder: TopLevelFolder, include_central: bool
    ) -> InterfaceOutput:
        """Return the next subject ID in the project."""
        try:
            next_sub = self.project.get_next_sub(
                top_level_folder,
                return_with_prefix=True,
                include_central=include_central,
            )
            return True, next_sub
        except BaseException as e:
            return False, str(e)

    def get_next_ses(
        self, top_level_folder: TopLevelFolder, sub: str, include_central: bool
    ) -> InterfaceOutput:
        """Return the next session ID for the `sub` in the project."""
        try:
            next_ses = self.project.get_next_ses(
                top_level_folder,
                sub,
                return_with_prefix=True,
                include_central=include_central,
            )
            return True, next_ses
        except BaseException as e:
            return False, str(e)

    def get_ssh_hostkey(self) -> InterfaceOutput:
        """Return the SSH remote server host key."""
        try:
            key = ssh.get_remote_server_key(
                self.project.cfg["central_host_id"]
            )
            return True, key
        except BaseException as e:
            return False, str(e)

    def save_hostkey_locally(self, key: paramiko.RSAKey) -> InterfaceOutput:
        """Save the SSH hostkey to disk."""
        try:
            ssh.save_hostkey_locally(
                key,
                self.project.cfg["central_host_id"],
                self.project.cfg.hostkeys_path,
            )
            return True, None

        except BaseException as e:
            return False, str(e)

    def setup_key_pair_and_rclone_config(
        self, password: str
    ) -> InterfaceOutput:
        """Set up SSH key pair and associated rclone configuration."""
        try:
            rsa_key, private_key_str = ssh.generate_ssh_key_strings()

            ssh.add_public_key_to_central_authorized_keys(
                self.project.cfg, rsa_key, password, log=False
            )
            self.project._setup_rclone_central_ssh_config(
                private_key_str, log=False
            )

            rclone.check_successful_connection_and_raise_error_on_fail(
                self.project.cfg
            )

            return True, None

        except BaseException as e:
            return False, str(e)

    # Setup Google Drive
    # ----------------------------------------------------------------------------------

    def setup_gdrive_connection(
        self,
        gdrive_client_secret: Optional[str] = None,
        config_token: Optional[str] = None,
    ) -> InterfaceOutput:
        """Try to set up and validate connection to Google Drive.

        This is done by running the rclone setup function which returns a
        subprocess.Popen object. The process object is stored in
        `self.gdrive_rclone_setup_process` to allow for termination
        of the process if needed. The `self.gdrive_setup_process_killed`
        flag is set to false to signal normal operation. The process is then
        awaited to ensure it completes successfully. If the process is killed
        manually, the `self.gdrive_setup_process_killed` flag is set to True
        to prevent raising an error when the process is killed.
        """
        try:
            process = self.project._setup_rclone_gdrive_config(
                gdrive_client_secret, config_token
            )
            self.gdrive_rclone_setup_process = process
            self.gdrive_setup_process_killed = False

            self.await_successful_gdrive_connection_setup_raise_on_fail(
                process
            )

            return True, None
        except BaseException as e:
            return False, str(e)

    def get_rclone_message_for_gdrive_without_browser(
        self, gdrive_client_secret: Optional[str] = None
    ) -> InterfaceOutput:
        """Get the rclone message for Google Drive setup without a browser."""
        try:
            output = gdrive.preliminary_for_setup_without_browser(
                self.project.cfg,
                gdrive_client_secret,
                self.project.cfg.get_rclone_config_name("gdrive"),
                log=False,
            )
            return True, output
        except BaseException as e:
            return False, str(e)

    def terminate_gdrive_setup(self) -> None:
        """Terminate rclone setup for Google Drive by killing the rclone process."""
        assert self.gdrive_rclone_setup_process is not None

        process = self.gdrive_rclone_setup_process

        # Check if the process is still running
        if process.poll() is None:
            self.gdrive_setup_process_killed = True
            process.kill()

    def await_successful_gdrive_connection_setup_raise_on_fail(
        self, process: subprocess.Popen
    ):
        """Wait for rclone setup for Google Drive to finish and verify successful connection.

        The `self.gdrive_setup_process_killed` flag helps prevent raising errors in case the
        process was killed manually.
        """
        stdout, stderr = process.communicate()

        if not self.gdrive_setup_process_killed:
            if process.returncode != 0:
                utils.raise_error(stderr.decode("utf-8"), ConnectionError)

            rclone.check_successful_connection_and_raise_error_on_fail(
                self.project.cfg
            )

    # Setup AWS
    # ----------------------------------------------------------------------------------

    def setup_aws_connection(
        self, aws_secret_access_key: str
    ) -> InterfaceOutput:
        """Set up the Amazon Web Service connection."""
        try:
            self.project._setup_rclone_aws_config(
                aws_secret_access_key, log=False
            )
            rclone.check_successful_connection_and_raise_error_on_fail(
                self.project.cfg
            )
            aws.raise_if_bucket_absent(self.project.cfg)
            return True, None
        except BaseException as e:
            return False, str(e)
