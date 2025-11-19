from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from pathlib import Path

    from datashuttle.utils.custom_types import (
        OverwriteExistingFiles,
    )

import yaml

from datashuttle.configs import canonical_folders
from datashuttle.utils import rclone_encryption, utils


class RCloneConfigs:
    """Class to manage the RClone configuration file.

    This is a file that RClone creates to hold all information about local and
    remote transfer targets. For example, the ssh RClone config holds the private key.

    In datashuttle, local filesystem configs uses the Rclone default configuration file,
    that RClone manages. However, remote transfers to ssh, aws and gdrive are held in
    separate config files (set using RClone's --config argument). Then being separate
    means these files can be separately encrypted.

    This class tracks the state on whether a RClone config is encrypted, as well
    as provides the default names for the rclone conf (e.g. central_<project_name>_<connection_method>).

    Parameters
    ----------
    config_base_class
        Path to the datashuttle configs folder where all configs for the project are stored.

    """

    def __init__(self, datashuttle_configs, config_base_path):
        """Construct the class."""
        self.datashuttle_configs = datashuttle_configs
        self.rclone_encryption_state_file_path = (
            config_base_path / "rclone_ps_state.yaml"
        )

    def load_rclone_config_is_encrypted(self) -> dict:
        """Track whether the Rclone config file is encrypted.

        This could be read directly from the RClone config file, but requires
        a subprocess call which can be slow on Windows. As this function is
        called a lot, we track this explicitly when a rclone config is
        encrypted / unencrypted and store to disk between sessions.
        """
        assert rclone_encryption.connection_method_requires_encryption(
            self.datashuttle_configs["connection_method"]
        )

        if self.rclone_encryption_state_file_path.is_file():
            with open(self.rclone_encryption_state_file_path, "r") as file:
                rclone_config_is_encrypted = yaml.full_load(file)
        else:
            rclone_config_is_encrypted = {
                "ssh": False,
                "gdrive": False,
                "aws": False,
            }

            with open(self.rclone_encryption_state_file_path, "w") as file:
                yaml.dump(rclone_config_is_encrypted, file)

        return rclone_config_is_encrypted

    def set_rclone_config_encryption_state(self, value: bool) -> None:
        """Store the current state of the rclone config encryption for the `connection_method`.

        Note that this is stored to disk each call (rather than tracked locally) to ensure
        it is updated live if updated through the Python API while the TUI is also running.
        """
        assert rclone_encryption.connection_method_requires_encryption(
            self.datashuttle_configs["connection_method"]
        )

        rclone_config_is_encrypted = self.load_rclone_config_is_encrypted()

        rclone_config_is_encrypted[
            self.datashuttle_configs["connection_method"]
        ] = value

        with open(self.rclone_encryption_state_file_path, "w") as file:
            yaml.dump(rclone_config_is_encrypted, file)

    def get_rclone_config_encryption_state(
        self,
    ) -> dict:
        """Return whether the config file associated with the current `connection_method`."""
        assert rclone_encryption.connection_method_requires_encryption(
            self.datashuttle_configs["connection_method"]
        )

        rclone_config_is_encrypted = self.load_rclone_config_is_encrypted()

        return rclone_config_is_encrypted[
            self.datashuttle_configs["connection_method"]
        ]

    def get_rclone_config_name(
        self, connection_method: Optional[str] = None
    ) -> str:
        """Generate the rclone configuration name for the central project."""
        if connection_method is None:
            connection_method = self.datashuttle_configs["connection_method"]

        return f"central_{self.datashuttle_configs.project_name}_{connection_method}"

    def get_rclone_central_connection_config_filepath(self) -> Path:
        """Return the full filepath to the rclone `.conf` config file."""
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

    def delete_existing_rclone_config_file(self) -> None:
        """Delete the Rclone config file if it exists."""
        rclone_config_filepath = (
            self.get_rclone_central_connection_config_filepath()
        )

        if rclone_config_filepath.exists():
            rclone_config_filepath.unlink()
            self.set_rclone_config_encryption_state(False)
