import fnmatch
import getpass
import stat
from pathlib import Path
from typing import List, Optional

import paramiko

from datashuttle.configs.configs import Configs

from . import utils

# --------------------------------------------------------------------------------------------------------------------
# SSH
# --------------------------------------------------------------------------------------------------------------------


def setup_ssh_key(
    ssh_key_path: Path,
    hostkeys: Path,
    cfg: Configs,
) -> None:
    """
    Set up an SSH private / public key pair with
    remote server. First, a private key is generated
    in the appdir. Next a connection requiring input
    password made, and the public part of the key
    added to ~/.ssh/authorized_keys.
    """
    """
            Setup an SSH private / public key pair with
            remote server. First, a private key is generated
            in the appdir. Next a connection requiring input
            password made, and the public part of the key
            added to ~/.ssh/authorized_keys.
            """
    generate_and_write_ssh_key(ssh_key_path)

    password = getpass.getpass(
        "Please enter password to your remote host to add the public key. "
        "You will not have to enter your password again."
    )

    key = paramiko.RSAKey.from_private_key_file(ssh_key_path.as_posix())

    add_public_key_to_remote_authorized_keys(cfg, hostkeys, password, key)

    utils.message_user(
        f"SSH key pair setup successfully. "
        f"Private key at: {ssh_key_path.as_posix()}"
    )


def connect_client(
    client: paramiko.SSHClient,
    cfg: Configs,
    hostkeys: Path,
    password: Optional[str] = None,
    private_key_path: Optional[Path] = None,
) -> None:
    """
    Connect client to remote server using paramiko.
    Accept either password or path to private key, but not both.
    Paramiko does not support pathlib.
    """
    try:
        client.get_host_keys().load(hostkeys.as_posix())
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            cfg["remote_host_id"],
            username=cfg["remote_host_username"],
            password=password,
            key_filename=private_key_path.as_posix()
            if isinstance(private_key_path, Path)
            else None,
            look_for_keys=True,
        )
    except Exception:
        utils.raise_error(
            "Could not connect to server. Ensure that \n"
            "1) You are on VPN network if required. \n"
            "2) The remote_host_id: {cfg['remote_host_id']} is"
            " correct.\n"
            "3) The remote username:"
            f" {cfg['remote_host_username']}, and password are correct."
        )


def add_public_key_to_remote_authorized_keys(
    cfg: Configs, hostkeys: Path, password: str, key: paramiko.RSAKey
) -> None:
    """
    Append the public part of key to remote server ~/.ssh/authorized_keys.
    """
    with paramiko.SSHClient() as client:
        connect_client(client, cfg, hostkeys, password=password)

        client.exec_command("mkdir -p ~/.ssh/")
        client.exec_command(
            # double >> for concatenate
            f'echo "{key.get_name()} {key.get_base64()}" '
            f">> ~/.ssh/authorized_keys"
        )
        client.exec_command("chmod 644 ~/.ssh/authorized_keys")
        client.exec_command("chmod 700 ~/.ssh/")


def verify_ssh_remote_host(remote_host_id: str, hostkeys: Path) -> bool:
    """
    Similar to connecting with other SSH manager e.g. putty,
    get the server key and present when connecting
    for manual validation.
    """
    with paramiko.Transport(remote_host_id) as transport:
        transport.connect()
        key = transport.get_remote_server_key()

    input_ = utils.get_user_input(
        f"The host key is not cached for this server:"
        f" {remote_host_id}.\nYou have no guarantee "
        f"that the server is the computer you think it is.\n"
        f"The server's {key.get_name()} key fingerprint is: "
        f"{key.get_base64()}\nIf you trust this host, to connect"
        " and cache the host key, press y: "
    )

    if input_ == "y":
        client = paramiko.SSHClient()
        client.get_host_keys().add(remote_host_id, key.get_name(), key)
        client.get_host_keys().save(hostkeys.as_posix())
        success = True
    else:
        utils.message_user("Host not accepted. No connection made.")
        success = False

    return success


def generate_and_write_ssh_key(ssh_key_path: Path) -> None:
    key = paramiko.RSAKey.generate(4096)
    key.write_private_key_file(ssh_key_path.as_posix())


def search_ssh_remote_for_directories(
    search_path: Path,
    search_prefix: str,
    cfg: Configs,
    hostkeys: Path,
    ssh_key_path: Path,
) -> List[str]:
    """
    Search for the search prefix in the search path over SSH.
    Returns the list of matching directories, files are filtered out.
    """
    with paramiko.SSHClient() as client:
        connect_client(client, cfg, hostkeys, private_key_path=ssh_key_path)

        sftp = client.open_sftp()

        all_dirnames = get_list_of_directory_names_over_sftp(
            sftp, search_path, search_prefix
        )

    return all_dirnames


def get_list_of_directory_names_over_sftp(
    sftp, search_path: Path, search_prefix: str
) -> List[str]:

    all_dirnames = []
    try:
        for file_or_dir in sftp.listdir_attr(search_path.as_posix()):

            if stat.S_ISDIR(file_or_dir.st_mode):

                if fnmatch.fnmatch(file_or_dir.filename, search_prefix):
                    all_dirnames.append(file_or_dir.filename)

    except FileNotFoundError:
        utils.raise_error(f"No file found at {search_path.as_posix()}")

    return all_dirnames
