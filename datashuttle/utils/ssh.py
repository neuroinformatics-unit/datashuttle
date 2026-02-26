from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from datashuttle.configs.config_class import Configs

from io import StringIO
from typing import Optional

import paramiko

from datashuttle.configs import canonical_configs
from datashuttle.utils import utils

# -----------------------------------------------------------------------------
# Setup SSH - API Wrappers
# -----------------------------------------------------------------------------
# These functions wrap core SSH setup functions for the API. See
# tui/screens/setup_ssh for the TUI equivalents.


def verify_ssh_central_host_api(
    central_host_id: str, hostkeys_path: Path, log: bool = True
) -> bool:
    """Prompt the user to verify and cache the SSH server's host key.

    This function retrieves the SSH server's key and asks the user to
    manually validate and accept it. Accepting the key caches it locally
    to ensure secure future connections.

    Parameters
    ----------
    central_host_id
        Hostname or IP address of the SSH server.

    hostkeys_path
        Path to the local file where known host keys are stored.

    log
        Whether to log the verification messages.

    Returns
    -------
    bool
        True if the host key was accepted and saved, False otherwise.

    """
    key = get_remote_server_key(central_host_id)

    message = (
        f"The host key is not cached for this server: "
        f"{central_host_id}.\nYou have no guarantee "
        f"that the server is the computer you think it is.\n"
        f"The server's {key.get_name()} key fingerprint is: "
        f"{key.get_base64()}\nIf you trust this host, to connect"
        f" and cache the host key, press y: "
    )
    input_ = utils.get_user_input(message)

    if input_ == "y":
        save_hostkey_locally(key, central_host_id, hostkeys_path)
        success = True
        utils.print_message_to_user("Host accepted.")
    else:
        utils.print_message_to_user("Host not accepted. No connection made.")
        success = False

    if log:
        if success:
            utils.log(f"{message}")
            utils.log(f"Hostkeys saved at:{hostkeys_path.as_posix()}")
        else:
            utils.log("Host not accepted. No connection made.")

    return success


def setup_ssh_key_api(
    cfg: Configs,
    log: bool = True,
) -> str:
    """Set up an SSH private / public key pair with central server.

    First, a private key is generated. Next a connection requiring input
    password made, and the public part of the key added to ~/.ssh/authorized_keys.
    The private key is returned so it can be stored in the Rclone config.

    Parameters
    ----------
    cfg
        datashuttle config UserDict

    log
        log if True, logger must already be initialised.

    """
    rsa_key, private_key = generate_ssh_key_strings()

    server_password = utils.get_connection_secret_from_user(
        connection_method_name="SSH",
        key_name_full="password",
        key_name_short="password",
        key_info=(
            "You are required to enter the password to your central host to add the public key. "
            "You will not have to enter your password again."
        ),
        log_status=log,
    )

    add_public_key_to_central_authorized_keys(cfg, rsa_key, server_password)

    return private_key


# -----------------------------------------------------------------------------
# Core Functions
# -----------------------------------------------------------------------------
# These functions are called by both API and TUI.
# Unfortunately it is not possible for TUI to call API directly in the case of
# setting up SSH, because it requires user input to proceed.


def add_public_key_to_central_authorized_keys(
    cfg: Configs, rsa_key: paramiko.RSAKey, server_password: str, log=True
) -> None:
    """Append the public part of key to central server ~/.ssh/authorized_keys.

    Parameters
    ----------
    cfg
        Datashuttle Configs object.

    rsa_key
        The RSAKey key, the public part to add to `~/.ssh/authorized_keys.`

    server_password
        Password to the central server.

    log
        If `True`, log the client connection process.

    """
    client: paramiko.SSHClient
    with paramiko.SSHClient() as client:
        connect_client(client, cfg, password=server_password, log=log)

        client.exec_command("mkdir -p ~/.ssh/")
        client.exec_command(
            # double >> for concatenate
            f'echo "{rsa_key.get_name()} {rsa_key.get_base64()}" '
            f">> ~/.ssh/authorized_keys"
        )
        client.exec_command("chmod 644 ~/.ssh/authorized_keys")
        client.exec_command("chmod 700 ~/.ssh/")


def generate_ssh_key_strings():
    """Generate a private and public SSH key pair."""
    rsa_key = generate_ssh_key()

    private_key_io = StringIO()
    rsa_key.write_private_key(private_key_io)

    private_key_io.seek(0)

    private_key_str = private_key_io.read()

    return rsa_key, private_key_str


def generate_ssh_key() -> paramiko.RSAKey:
    """Generate an RSA SSH key."""
    return paramiko.RSAKey.generate(4096)


def connect_client(
    client: paramiko.SSHClient,
    cfg: Configs,
    password: Optional[str] = None,
    log=True,
) -> None:
    """Connect client to central server using paramiko."""
    try:
        client.get_host_keys().load(cfg.hostkeys_path.as_posix())
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

        client.connect(
            cfg["central_host_id"],
            username=cfg["central_host_username"],
            password=password,
            key_filename=None,
            look_for_keys=True,
            port=canonical_configs.get_default_ssh_port(),
        )

        utils.print_message_to_user(
            f"Connection to {cfg['central_host_id']} made successfully."
        )

    except Exception as e:
        raise_func = utils.log_and_raise_error if log else utils.raise_error

        raise_func(
            f"Could not connect to server. Ensure that \n"
            f"1) You have run setup_ssh_connection() \n"
            f"2) You are on VPN network if required. \n"
            f"3) The central_host_id: {cfg['central_host_id']} is"
            f" correct.\n"
            f"4) The central username:"
            f" {cfg['central_host_username']}, and password are correct.\n\n"
            f"Original error: {e}",
            ConnectionError,
        )


def save_hostkey_locally(key, central_host_id, hostkeys_path) -> None:
    """Save the SSH host key locally to the specified hostkeys file.

    The host key uniquely identifies the SSH server to prevent
    man-in-the-middle attacks by verifying the server's identity
    on future connections.

    Parameters
    ----------
    key
        The SSH host key to save.

    central_host_id
        The hostname or IP address of the central host.

    hostkeys_path
        The file path where host keys are stored locally.

    """
    client = paramiko.SSHClient()

    port = canonical_configs.get_default_ssh_port()
    host_key = f"[{central_host_id}]:{port}" if port != 22 else central_host_id

    client.get_host_keys().add(
        host_key,
        key.get_name(),
        key,
    )
    client.get_host_keys().save(hostkeys_path.as_posix())


def get_remote_server_key(central_host_id: str):
    """Get the remove server host key for validation before connection.

    Parameters
    ----------
    central_host_id
        The hostname or IP address of the central host.

    """
    transport: paramiko.Transport
    with paramiko.Transport(
        (central_host_id, canonical_configs.get_default_ssh_port())
    ) as transport:
        transport.connect()
        key = transport.get_remote_server_key()

    return key
