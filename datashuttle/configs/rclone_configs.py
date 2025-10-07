from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from datashuttle.utils.custom_types import (
        OverwriteExistingFiles,
    )

from pathlib import Path

import yaml

from datashuttle.configs import canonical_folders
from datashuttle.utils import utils


class RCloneConfigs:
    """This class manages the RClone configuration file. This is a file that RClone creates
    to hold all information about local and remote transfer targets. For example, the
    ssh RClone config holds the private key.

    In datashuttle, local filesystem configs uses the Rclone default configuration file,
    that RClone manages. However, remote transfers to ssh, aws and gdrive are held in
    separate config files (set using RClone's --config argument). Then being separate
    means passwords can be set on these files.

    This class tracks the state on whether a RClone config has a password, as well
    as provides the default names for the rclone conf (e.g. central_<project_name>_<connection_method>).

    Parameters
    ----------
    config_base_class
        Path to the datashuttle configs folder where all configs for the project are stored.

    """

    def __init__(self, datashuttle_configs, config_base_path):
        self.datashuttle_configs = datashuttle_configs
        self.rclone_password_state_file_path = (
            config_base_path / "rclone_ps_state.yaml"
        )

    def load_rclone_has_password(self):
        """Track whether the Rclone config file has a password set. This could be
        read directly from the RClone config file, but requires a subprocess call
        which can be slow on Windows. As this function is called a lot, we track
        this explicitly when a rclone config password is set / removed
        and store to disk between sessions.
        """
        assert self.datashuttle_configs["connection_method"] in [
            "ssh",
            "aws",
            "gdrive",
        ]

        if self.rclone_password_state_file_path.is_file():
            with open(self.rclone_password_state_file_path, "r") as file:
                rclone_has_password = yaml.full_load(file)
        else:
            rclone_has_password = {
                "ssh": False,
                "gdrive": False,
                "aws": False,
            }

            with open(self.rclone_password_state_file_path, "w") as file:
                yaml.dump(rclone_has_password, file)

        return rclone_has_password

    def set_rclone_has_password(self, value):
        """Store the current state of the rclone config file password for the `connection_method`.

        Note that this is stored to disk each call (rather than tracked locally) to ensure
        it is updated live if updated through the Python API while the TUI is also running.
        """
        assert self.datashuttle_configs["connection_method"] in [
            "ssh",
            "aws",
            "gdrive",
        ]

        rclone_has_password = self.load_rclone_has_password()

        rclone_has_password[self.datashuttle_configs["connection_method"]] = (
            value
        )

        with open(self.rclone_password_state_file_path, "w") as file:
            yaml.dump(rclone_has_password, file)

    def get_rclone_has_password(
        self,
    ):
        """Return whether the config file associated with the current `connection_method`."""
        rclone_has_password = self.load_rclone_has_password()

        return rclone_has_password[
            self.datashuttle_configs["connection_method"]
        ]

    def get_rclone_config_name(
        self, connection_method: Optional[str] = None
    ) -> str:
        """Generate the rclone configuration name for the central project."""
        if connection_method is None:
            connection_method = self.datashuttle_configs["connection_method"]

        return f"central_{self.datashuttle_configs.project_name}_{connection_method}"

    def get_rclone_config_filepath(self) -> Path:
        """The full filepath to the rclone `.conf` config file"""
        return (
            canonical_folders.get_rclone_config_base_path()
            / f"{self.get_rclone_config_name()}.conf"
        )

    def make_rclone_transfer_options(
        self, overwrite_existing_files: OverwriteExistingFiles, dry_run: bool
    ) -> Dict:
        """Create a dictionary of rclone transfer options."""
        allowed_overwrite = ["never", "always", "if_source_newer"]

        if overwrite_existing_files not in allowed_overwrite:
            utils.log_and_raise_error(
                f"`overwrite_existing_files` not "
                f"recognised, must be one of: "
                f"{allowed_overwrite}",
                ValueError,
            )

        return {
            "overwrite_existing_files": overwrite_existing_files,
            "show_transfer_progress": True,
            "transfer_verbosity": "vv",
            "dry_run": dry_run,
        }
