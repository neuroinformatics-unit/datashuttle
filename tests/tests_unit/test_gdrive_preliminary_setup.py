import base64
import json
from typing import Dict

import pytest

from datashuttle.utils import rclone


class TestGdrivePreliminarySetup:
    @pytest.mark.parametrize(
        "client_id", ["client-id-1", "some-random-client-id-2"]
    )
    @pytest.mark.parametrize("root_folder_id", ["folder-id-1", "folder-id-2"])
    @pytest.mark.parametrize("client_secret", ["secret-1", "some-secret-2"])
    def test_preliminary_setup_for_gdrive(
        self, client_id, root_folder_id, client_secret
    ):
        """Test the outputs of `preliminary_setup_gdrive_config_without_browser` and check
        that they contain the correct credentials in the encoded format.
        """
        from collections import UserDict
        from pathlib import Path

        class MockConfigs(UserDict):
            def __init__(self, client_id_, root_folder_id_):
                super(MockConfigs, self).__init__()
                self.data["gdrive_client_id"] = client_id_
                self.data["gdrive_root_folder_id"] = root_folder_id_
                self.data["connection_method"] = "drive"

                class RClone:
                    def delete_existing_rclone_config_file(self):
                        pass

                    def get_rclone_central_connection_config_filepath(self):
                        return Path("")

                self.rclone = RClone()

        mock_configs = MockConfigs(client_id, root_folder_id)

        output = rclone.preliminary_setup_gdrive_config_without_browser(
            mock_configs, client_secret, "test_gdrive_preliminary"
        )

        assert (
            "Execute the following on the machine with the web browser"
            in output
        )
        assert 'rclone authorize "drive"' in output

        connection_credential_string = (
            output.split('rclone authorize "drive"')[-1]
            .split("Then paste the result")[0]
            .strip()
        )
        connection_credential_string = connection_credential_string.strip('"')
        credentials_dict = self.get_decoded_dict_from_base64(
            connection_credential_string
        )

        assert "client_id" in credentials_dict
        assert credentials_dict["client_id"] == client_id

        assert "root_folder_id" in credentials_dict
        assert credentials_dict["root_folder_id"] == root_folder_id

        assert "client_secret" in credentials_dict
        assert credentials_dict["client_secret"] == client_secret

    def get_decoded_dict_from_base64(
        self, base64_string: str
    ) -> Dict[str, str]:
        """Decode a base64 string and return the encoded dictionary."""
        base64_string = base64_string.strip().rstrip("=")

        padding_needed = 4 - (len(base64_string) % 4)

        if padding_needed != 4:  # Only add padding if needed
            base64_string += "=" * padding_needed

        decoded_bytes = base64.b64decode(base64_string)

        decoded_str = decoded_bytes.decode("utf-8")
        data = json.loads(decoded_str)

        return data
