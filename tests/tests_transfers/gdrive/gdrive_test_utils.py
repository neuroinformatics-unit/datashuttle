import os
from pathlib import Path

import pytest

from datashuttle import DataShuttle
from datashuttle.configs import canonical_configs
from datashuttle.utils import rclone


def setup_project_for_gdrive(tmp_path):
    """
    Setup a project in tmp_path and setup the GDrive remote.
    Then copy the config folder that contains the rclone.conf
    to the config folder. Finally, set the central path
    to gdrive (i.e. the name from the rclone.conf).

    Returns the project object and config name.
    """
    # Check if required environment variables are set
    if not has_gdrive_environment_variables():
        pytest.skip("Google Drive environment variables not set")

    project_name = "test_project"
    local_path = tmp_path / "local"

    project = DataShuttle(project_name)
    project.make_config_file(local_path, "")
    project.update_config_file("central_host_id", "gdrive")
    project.update_config_file("central_host_type", "remote")

    config_path = canonical_configs.get_config_path() / project_name

    copy_rclone_config_to_project(config_path)

    assert (
        has_gdrive_environment_variables()
    ), "Environment variables to setup GDrive remote not found. Contact an Admin."

    return project, project_name


def copy_rclone_config_to_project(config_path):
    """
    Copy the rclone config from the base directory
    (that contains environment-variable set credentials)
    to the datashuttle config folder.
    """
    rclone_config_path = config_path / "rclone"

    rclone_config_path.mkdir(parents=True)

    Path(rclone_config_path / "rclone.conf").write_text(
        make_rclone_config_contents()
    )


def has_gdrive_environment_variables():
    """
    The expected environment variables are set only on the
    'neuroinformatics' repo. Contact Joe@SWC for access.
    """
    keys = ["SERVICE_ACCOUNT_KEY", "ROOT_FOLDER_ID"]

    for key in keys:
        if key not in os.environ:
            return False
        
        # On CI triggered by forked repositories, secrets are empty
        if os.environ[key].strip() == "":
            return False

    return True


def make_rclone_config_contents():
    """"""
    contents = f"""
[gdrive]
type = drive
scope = drive
service_account_credentials = {os.environ["SERVICE_ACCOUNT_KEY"]}
root_folder_id = {os.environ["ROOT_FOLDER_ID"]}
    """
    return contents


def setup_gdrive_project_and_upload_folder(tmp_path):
    """
    Setup the GDrive project, make a local folder containing
    subjects / sessions and upload this to GDrive.

    Returns the project, project_name, and the name of the uploaded
    sub / ses.
    """
    project, project_name = setup_project_for_gdrive(tmp_path)
    project.create_folders(
        "all",
        "sub-001",
        "all",
        "ses-001",
    )
    project.upload_entire_project()

    return project, project_name


def teardown_project(project, on_fail="error"):
    """
    First, attempt to clean up the central project if one has
    been made. Then, remove the local configs from the local config folder.
    """
    if project.get_central_path().is_dir():
        project_path_to_delete = project.get_central_path()

        try:
            rclone.delete(project.cfg, project_path_to_delete)
        except rclone.RcloneError as e:
            if on_fail == "error":
                raise e
            elif on_fail == "warn":
                print(f"Could not remove {project_path_to_delete}")

    # Always cleanup configs
    configs_path = canonical_configs.get_config_path() / project.project_name

    if configs_path.is_dir():
        rclone.delete_local_folder(configs_path)
