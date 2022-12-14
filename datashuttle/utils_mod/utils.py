import datetime
import fnmatch
import glob
import os
import re
import stat
import warnings
from pathlib import Path
from typing import Optional, Union

import appdirs
import paramiko

# --------------------------------------------------------------------------------------------------------------------
# Directory Utils
# --------------------------------------------------------------------------------------------------------------------


def make_dirs(paths: Union[Path, list]):
    """
    For path or list of path, make them if
    they do not already exist.
    """
    if isinstance(paths, Path):
        paths = [paths]

    for path_ in paths:

        if not path_.is_dir():
            path_.mkdir(parents=True)
        else:
            warnings.warn(
                "The following directory was not made "
                "because it already exists"
                f" {path_.as_posix()}"
            )


def make_datashuttle_metadata_folder(full_path: Path):
    meta_folder_path = full_path / ".datashuttle_meta"
    make_dirs(meta_folder_path)


def search_filesystem_path_for_directories(
    search_path_with_prefix: Path,
) -> list:
    """
    Use glob to search the full search path (including prefix) with glob.
    Files are filtered out of results, returning directories only.
    """
    all_dirnames = []
    for file_or_dir in glob.glob(search_path_with_prefix.as_posix()):
        if os.path.isdir(file_or_dir):
            all_dirnames.append(os.path.basename(file_or_dir))
    return all_dirnames


# --------------------------------------------------------------------------------------------------------------------
# SSH
# --------------------------------------------------------------------------------------------------------------------


def connect_client(
    client: paramiko.SSHClient,
    cfg,
    hostkeys: Path,
    password: Optional[str] = None,
    private_key_path: Optional[Path] = None,
):
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
        raise_error(
            "Could not connect to server. Ensure that \n"
            "1) You are on VPN network if required. \n"
            "2) The remote_host_id: {cfg['remote_host_id']} is"
            " correct.\n"
            "3) The remote username:"
            f" {cfg['remote_host_username']}, and password are correct."
        )


def add_public_key_to_remote_authorized_keys(
    cfg, hostkeys: Path, password: str, key: paramiko.RSAKey
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


def verify_ssh_remote_host(remote_host_id: str, hostkeys: Path) -> bool:
    """"""
    with paramiko.Transport(remote_host_id) as transport:
        transport.connect()
        key = transport.get_remote_server_key()

    input_ = get_user_input(
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
        message_user("Host not accepted. No connection made.")
        success = False

    return success


def generate_and_write_ssh_key(ssh_key_path: Path):
    key = paramiko.RSAKey.generate(4096)
    key.write_private_key_file(ssh_key_path.as_posix())


def search_ssh_remote_for_directories(
    search_path: Path,
    search_prefix: str,
    cfg,
    hostkeys: Path,
    ssh_key_path: Path,
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
    sftp, search_path: Path, search_prefix: str
) -> list:

    all_dirnames = []
    try:
        for file_or_dir in sftp.listdir_attr(search_path.as_posix()):
            if stat.S_ISDIR(file_or_dir.st_mode):
                if fnmatch.fnmatch(file_or_dir.filename, search_prefix):
                    all_dirnames.append(file_or_dir.filename)
    except FileNotFoundError:
        raise_error(f"No file found at {search_path.as_posix()}")

    return all_dirnames


# --------------------------------------------------------------------------------------------------------------------
# General Utils
# --------------------------------------------------------------------------------------------------------------------


def message_user(message: Union[str, list]):
    """
    Centralised way to send message.
    """
    print(message)


def get_user_input(message) -> str:
    """
    Centralised way to get user input
    """
    input_ = input(message)
    return input_


def raise_error(message: str):
    """
    Temporary centralized way to raise and error
    """
    raise BaseException(message)


def get_appdir_path(project_name: str) -> Path:
    """
    It is not possible to write to program files in windows
    from app without admin permissions. However, if admin
    permission given drag and drop don't work, and it is
    not good practice. Use appdirs module to get the
    AppData cross-platform and save / load all files form here .
    """
    base_path = Path(appdirs.user_data_dir("DataShuttle")) / project_name

    if not base_path.is_dir():
        make_dirs(base_path)

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

    if isinstance(names, str):
        names = [names]

    if any([" " in ele for ele in names]):
        raise_error("sub or ses names cannot include spaces.")

    prefixed_names = ensure_prefixes_on_list_of_names(names, prefix)

    if len(prefixed_names) != len(set(prefixed_names)):
        raise_error(
            "Subject and session names but all be unique (i.e. there are no"
            " duplicates in list input)"
        )

    prefixed_names = update_names_with_range_to_flag(prefixed_names, prefix)

    update_names_with_datetime(prefixed_names)

    return prefixed_names


# Handle @TO flags  -------------------------------------------------------


def update_names_with_range_to_flag(names: list, prefix: str) -> list:
    """
    Given a list of names, check if they contain the @TO keyword.
    If so, expand to a range of names. Names including the @TO
    keyword must be in the form prefix-num1@num2. The maximum
    number of leading zeros are used to pad the output
    e.g.
    sub-01@003 becomes ["sub-001", "sub-002", "sub-003"]

    Input can also be a mixed list e.g.
    names = ["sub-01", "sub-02@TO04", "sub-05@TO10"]
    will output a list of ["sub-01", ..., "sub-10"]
    """
    new_names = []

    for i, name in enumerate(names):

        if "@TO" in name:

            check_name_is_formatted_correctly(name, prefix)

            prefix_tag = re.search(f"{prefix}[0-9]+@TO[0-9]+", name)[0]  # type: ignore
            tag_number = prefix_tag.split(f"{prefix}")[1]

            name_start_str, name_end_str = name.split(tag_number)

            if "@TO" not in tag_number:
                raise_error(
                    f"@TO flag must be between two numbers in the {prefix} tag."
                )

            left_number, right_number = tag_number.split("@TO")

            if int(left_number) >= int(right_number):
                raise_error(
                    "Number of the subject to the  left of @TO flag "
                    "must be small than number to the right."
                )

            names_with_new_number_inserted = (
                make_list_of_zero_padded_names_across_range(
                    left_number, right_number, name_start_str, name_end_str
                )
            )
            new_names += names_with_new_number_inserted

        else:
            new_names.append(name)

    return new_names


def check_name_is_formatted_correctly(name: str, prefix: str):
    """
    Check the input string is formatted with the @TO key
    as expected.
    """
    first_key_value_pair = name.split("_")[0]
    expected_format = re.compile(f"{prefix}[0-9]+@TO[0-9]+")

    if not re.fullmatch(expected_format, first_key_value_pair):
        raise_error(
            f"The name: {name} is not in required format for @TO keyword. "
            f"The start must be  be {prefix}<NUMBER>@TO<NUMBER>)"
        )


def make_list_of_zero_padded_names_across_range(
    left_number: str, right_number: str, name_start_str: str, name_end_str: str
) -> list:
    """
    Numbers formatted with the @TO keyword need to have
    standardised leading zeros on the output. Here we take
    the maximum number of leading zeros and apply or
    all numbers in the range.
    """
    max_leading_zeros = max(
        num_leading_zeros(left_number), num_leading_zeros(right_number)
    )

    all_numbers = [*range(int(left_number), int(right_number) + 1)]

    all_numbers_with_leading_zero = [
        str(number).zfill(max_leading_zeros + 1) for number in all_numbers
    ]

    names_with_new_number_inserted = [
        f"{name_start_str}{number}{name_end_str}"
        for number in all_numbers_with_leading_zero
    ]

    return names_with_new_number_inserted


def num_leading_zeros(string: str):
    """int() strips leading zeros"""
    return len(string) - len(str(int(string)))


# Handle @DATE, @DATETIME, @TIME flags -------------------------------------------------


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


def add_underscore_before_after_if_not_there(string: str, key: str) -> str:
    """
    If names are passed with @DATE, @TIME, or @DATETIME
    but not surrounded by underscores, check and insert
    if required. e.g. sub-001@DATE becomes sub-001_@DATE
    or sub-001@DATEid-101 becomes sub-001_@DATE_id-101
    """
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
    """
    Make sure all elements in the list of names are
    prefixed with the prefix typically "sub-" or "ses-"
    """
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


def raise_error_not_exists_or_not_yaml(path_to_config: Path):
    if not path_to_config.exists():
        raise_error(f"No file found at: {path_to_config}")

    if path_to_config.suffix not in [".yaml", ".yml"]:
        raise_error("The config file must be a YAML file")
