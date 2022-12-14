import datetime
import fnmatch
import glob
import os
import stat
import warnings
from pathlib import Path
from typing import Optional, Union

import appdirs
import paramiko

# --------------------------------------------------------------------------------------------------------------------
# Directory Utils
# --------------------------------------------------------------------------------------------------------------------


def make_dirs(paths: Union[str, list]):
    """
    For path or list of path, make them if
    do not already exist.
    """
    if isinstance(paths, str):
        paths = [paths]

    for path_ in paths:
        path_ = os.path.expanduser(path_)
        if not os.path.isdir(path_):
            os.makedirs(path_)
        else:
            warnings.warn(
                "The following directory was not made "
                "because it already exists"
                f" {path_}"
            )


def make_datashuttle_metadata_folder(full_path: str):
    meta_folder_path = full_path + "/.datashuttle_meta"
    make_dirs(meta_folder_path)


def search_filesystem_path_for_directories(
    search_path_with_prefix: str,
) -> list:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning directories only.
    """
    all_dirnames = []
    for file_or_dir in glob.glob(search_path_with_prefix):
        if os.path.isdir(file_or_dir):
            all_dirnames.append(os.path.basename(file_or_dir))
    return all_dirnames


# --------------------------------------------------------------------------------------------------------------------
# SSH
# --------------------------------------------------------------------------------------------------------------------


def connect_client(
    client: paramiko.SSHClient,
    cfg,  # cannot import Configs class due to circular import
    hostkeys: str,
    password: Optional[str] = None,
    private_key_path: Optional[str] = None,
):
    """
    Connect client to remote server using paramiko.
    Accept either password or path to private key, but not both.
    """
    try:
        client.get_host_keys().load(hostkeys)
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            cfg["remote_host_id"],
            username=cfg["remote_host_username"],
            password=password,
            key_filename=private_key_path,
            look_for_keys=True,
        )
    except Exception:
        raise_error(
            "Could not connect to server. Ensure that \n"
            "1) You are on VPN network if required. \n"
            "2) The remote_host_id: {cfg['remote_host_id']} is"
            " correct.\n"
            "3) The remote username:"
            f" {cfg['remote_host_username']}, and password are correct."
        )


def add_public_key_to_remote_authorized_keys(
    cfg, hostkeys: str, password: str, key: paramiko.RSAKey
):
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


def verify_ssh_remote_host(remote_host_id: str, hostkeys: str) -> bool:
    """"""
    with paramiko.Transport(remote_host_id) as transport:
        transport.connect()
        key = transport.get_remote_server_key()

    message_user(
        "The host key is not cached for this server:"
        f" {remote_host_id}.\nYou have no guarantee "
        f"that the server is the computer you think it is.\n"
        f"The server's {key.get_name()} key fingerprint is: "
        f"{key.get_base64()}\nIf you trust this host, to connect"
        " and cache the host key, press y: "
    )
    input_ = input()

    if input_ == "y":
        client = paramiko.SSHClient()
        client.get_host_keys().add(remote_host_id, key.get_name(), key)
        client.get_host_keys().save(hostkeys)
        sucess = True
    else:
        message_user("Host not accepted. No connection made.")
        sucess = False

    return sucess


def generate_and_write_ssh_key(ssh_key_path: str):
    key = paramiko.RSAKey.generate(4096)
    key.write_private_key_file(ssh_key_path)


def search_ssh_remote_for_directories(
    search_path: str,
    search_prefix: str,
    cfg,
    hostkeys: str,
    ssh_key_path: str,
) -> list:
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
    sftp, search_path: str, search_prefix: str
) -> list:

    all_dirnames = []
    try:
        for file_or_dir in sftp.listdir_attr(search_path):
            if stat.S_ISDIR(file_or_dir.st_mode):
                if fnmatch.fnmatch(file_or_dir.filename, search_prefix):
                    all_dirnames.append(file_or_dir.filename)
    except FileNotFoundError:
        raise_error(f"No file found at {search_path}")

    return all_dirnames


# --------------------------------------------------------------------------------------------------------------------
# General Utils
# --------------------------------------------------------------------------------------------------------------------


def message_user(message: str):
    """
    Centralised way to send message.
    """
    print(message)


def raise_error(message: str):
    """
    Temporary centralized way to raise and error
    """
    raise BaseException(message)


def get_appdir_path(project_name: str) -> Path:
    """
    It is not possible to write to programfiles in windows
    from app without admin permissions. However if admin
    permission given drag and drop dont work, and it is
    not good practice. Use appdirs module to get the
    AppData cross-platform and save / load all files form here .
    """
    base_path = Path(
        os.path.join(appdirs.user_data_dir("DataShuttle"), project_name)
    )

    if not os.path.isdir(base_path):
        os.makedirs(base_path)

    return base_path


def process_names(
    names: Union[list, str],
    prefix: str,
) -> Union[list, str]:
    """
    Check a single or list of input session or subject names.
    First check the type is correct, next prepend the prefix
    sub- or ses- to entries that do not have the relevant prefix.
    Finally, check for duplicates.

    :param names: str or list containing sub or ses names (e.g. to make dirs)
    :param prefix: "sub" or "ses" - this defines the prefix checks.
    """
    if type(names) not in [str, list] or any(
        [not isinstance(ele, str) for ele in names]
    ):
        raise_error(
            "Ensure subject and session names are list of strings, or string"
        )

    if any([" " in ele for ele in names]):
        raise_error("sub or ses names cannot include spaces.")

    if isinstance(names, str):
        names = [names]

    update_names_with_datetime(names)

    prefixed_names = ensure_prefixes_on_list_of_names(names, prefix)

    if len(prefixed_names) != len(set(prefixed_names)):
        raise_error(
            "Subject and session names but all be unqiue (i.e. there are no"
            " duplicates in list input)"
        )

    return prefixed_names


def update_names_with_datetime(names: list):
    """
    Replace @DATE and @DATETIME flag with date and datetime respectively.

    Format using key-value pair for bids, i.e. date-20221223_time-
    """
    date = str(datetime.datetime.now().date().strftime("%Y%m%d"))
    format_date = f"date-{date}"

    time_ = datetime.datetime.now().time().strftime("%H%M%S")
    format_time = f"time-{time_}"

    for i, name in enumerate(names):

        if "@DATETIME" in name:  # must come first
            name = add_underscore_before_after_if_not_there(name, "@DATETIME")
            datetime_ = f"{format_date}_{format_time}"
            names[i] = name.replace("@DATETIME", datetime_)

        elif "@DATE" in name:
            name = add_underscore_before_after_if_not_there(name, "@DATE")
            names[i] = name.replace("@DATE", format_date)

        elif "@TIME" in name:
            name = add_underscore_before_after_if_not_there(name, "@TIME")
            names[i] = name.replace("@TIME", format_time)


def add_underscore_before_after_if_not_there(string, key):

    key_len = len(key)
    key_start_idx = string.index(key)

    # Handle left edge
    if string[key_start_idx - 1] != "_":
        string_split = string.split(key)  # assumes key only in string once
        assert (
            len(string_split) == 2
        ), f"{key} must not appear in string more than once."

        string = f"{string_split[0]}_{key}{string_split[1]}"

    updated_key_start_idx = string.index(key)
    key_end_idx = updated_key_start_idx + key_len

    if key_end_idx != len(string) and string[key_end_idx] != "_":
        string = f"{string[:key_end_idx]}_{string[key_end_idx:]}"

    return string


def ensure_prefixes_on_list_of_names(
    names: Union[list, str], prefix: str
) -> list:
    """ """
    n_chars = len(prefix)
    return [
        prefix + name if name[:n_chars] != prefix else name for name in names
    ]


def get_path_after_base_dir(base_dir: Path, path_: Path) -> Path:
    """"""
    if path_already_stars_with_base_dir(base_dir, path_):
        return path_.relative_to(base_dir)
    return path_


def path_already_stars_with_base_dir(base_dir: Path, path_: Path) -> bool:
    return path_.as_posix().startswith(base_dir.as_posix())
