import os

from datashuttle.utils import rclone_encryption

from .. import test_utils
from ..base import BaseTest
from ..tests_transfers.ssh import ssh_test_utils


class TestRcloneEncryption(BaseTest):
    def test_set_and_remove_password(self, project):
        """ """
        ssh_test_utils.setup_project_for_ssh(
            project,
        )

        rclone_config_path = (
            project.cfg.rclone.get_rclone_central_connection_config_filepath()
        )

        if rclone_config_path.exists():
            rclone_config_path.unlink()

        import textwrap

        config_content = textwrap.dedent(f"""\
        [{project.cfg.rclone.get_rclone_config_name()}]
        type = sftp
        host = ssh.swc.ucl.ac.uk
        user = jziminski
        port = 22
        key_file = C:/Users/Jzimi/.datashuttle/my_project_name/my_project_name_ssh_key
        shell_type = unix
        md5sum_command = md5sum
        sha1sum_command = sha1sum
        """)

        # Write to file
        with open(rclone_config_path, "w") as file:
            file.write(config_content)

        rclone_encryption.run_rclone_config_encrypt(project.cfg)

        assert "RCLONE_PASSWORD_COMMAND" not in os.environ

        test_utils.check_rclone_file_is_encrypted(rclone_config_path)

        rclone_encryption.remove_rclone_encryption(project.cfg)

        assert "RCLONE_PASSWORD_COMMAND" not in os.environ

        with open(rclone_config_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        assert first_line == f"[{project.cfg.rclone.get_rclone_config_name()}]"
