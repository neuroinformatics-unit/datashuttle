import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Dict, List, Literal

from datashuttle.configs.config_class import Configs
from datashuttle.utils import utils
from datashuttle.utils.custom_types import TopLevelFolder


def call_rclone(command: str, pipe_std: bool = False) -> CompletedProcess:
    """
    Call rclone with the specified command. Current mode is double-verbose.
    Return the completed process from subprocess.

    Parameters
    ----------
    command: Rclone command to be run

    pipe_std: if True, do not output anything to stdout.
    """
    command = "rclone " + command
    if pipe_std:
        output = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
    else:
        output = subprocess.run(command, shell=True)

    return output


# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------


def setup_rclone_config_for_local_filesystem(
    rclone_config_name: str,
    log: bool = True,
):
    """
    RClone sets remote targets in a config file that are
    used at transfer. For local filesystem, this is essentially
    a placeholder and that is not linked to a particular filepath.
    It just tells rclone to use the local filesystem - then we
    supply the filepath at transfer time.

    For local filesystem, this is just a placeholder and
    the config contains no further information.

    For SSH, this contains information for
    connecting to central with SSH.

    Parameters
    ----------

    rclone_config_name : rclone config name
         canonical config name, generated by
         datashuttle.cfg.get_rclone_config_name()

    log : whether to log, if True logger must already be initialised.
    """
    call_rclone(f"config create {rclone_config_name} local", pipe_std=True)

    if log:
        log_rclone_config_output()


def setup_rclone_config_for_ssh(
    cfg: Configs,
    rclone_config_name: str,
    ssh_key_path: Path,
    log: bool = True,
):
    """
     RClone sets remote targets in a config file that are
     used at transfer. For SSH, this must contain the central path,
     username and ssh key. The relative path is supplied at transfer time.

     Parameters
     ----------

    cfg : Configs
       datashuttle configs UserDict.

    rclone_config_name : rclone config name
         canonical config name, generated by
         datashuttle.cfg.get_rclone_config_name()

    ssh_key_path : path to the ssh key used for connecting to
        ssh central filesystem,

    log : whether to log, if True logger must already be initialised.
    """
    call_rclone(
        f"config create "
        f"{rclone_config_name} "
        f"sftp "
        f"host {cfg['central_host_id']} "
        f"user {cfg['central_host_username']} "
        f"port 22 "
        f"key_file {ssh_key_path.as_posix()}",
        pipe_std=True,
    )

    if log:
        log_rclone_config_output()


def setup_rclone_config_for_gdrive(
    cfg: Configs,
    rclone_config_name: str,
    log: bool = True,
):
    client_id_key_value = (
        f"client_id {cfg['gdrive_client_id']} "
        if cfg["gdrive_client_id"]
        else " "
    )
    client_secret_key_value = (
        f"client_secret {cfg['gdrive_client_secret']} "
        if cfg["gdrive_client_secret"]
        else ""
    )
    call_rclone(
        f"config create "
        f"{rclone_config_name} "
        f"drive "
        f"{client_id_key_value}"
        f"{client_secret_key_value}"
        f"scope drive",
        pipe_std=True,
    )

    if log:
        log_rclone_config_output()


def log_rclone_config_output():
    output = call_rclone("config file", pipe_std=True)
    utils.log(
        f"Successfully created rclone config. "
        f"{output.stdout.decode('utf-8')}"
    )


def check_rclone_with_default_call() -> bool:
    """
    Check to see whether rclone is installed.
    """
    try:
        output = call_rclone("-h", pipe_std=True)
    except FileNotFoundError:
        return False
    return True if output.returncode == 0 else False


def prompt_rclone_download_if_does_not_exist() -> None:
    """
    Check that rclone is installed. If it does not
    (e.g. first time using datashuttle) then download.
    """
    if not check_rclone_with_default_call():
        raise BaseException(
            "RClone installation not found. Install by entering "
            "the following into your terminal:\n"
            " conda install -c conda-forge rclone"
        )


# -----------------------------------------------------------------------------
# Transfer
# -----------------------------------------------------------------------------


def transfer_data(
    cfg: Configs,
    upload_or_download: Literal["upload", "download"],
    top_level_folder: TopLevelFolder,
    include_list: List[str],
    rclone_options: Dict,
) -> subprocess.CompletedProcess:
    """
    Transfer data by making a call to Rclone.

    Parameters
    ----------

    cfg: Configs
        datashuttle configs

    upload_or_download : Literal["upload", "download"]
        If "upload", transfer from `local_path` to `central_path`.
        "download" proceeds in the opposite direction.

    top_level_folder: Literal["rawdata", "derivatives"]
        The top-level-folder to transfer files within.

    include_list : List[str]
        A list of filepaths to include in the transfer

    rclone_options : Dict
        A list of options to pass to Rclone's copy function.
        see `cfg.make_rclone_transfer_options()`.
    """
    assert upload_or_download in [
        "upload",
        "download",
    ], "must be 'upload' or 'download'"

    local_filepath = cfg.get_base_folder("local", top_level_folder).as_posix()

    central_filepath = cfg.get_base_folder(
        "central", top_level_folder
    ).as_posix()

    extra_arguments = handle_rclone_arguments(rclone_options, include_list)

    if upload_or_download == "upload":
        output = call_rclone(
            f"{rclone_args('copy')} "
            f'"{local_filepath}" "{cfg.get_rclone_config_name()}:'
            f'{central_filepath}" {extra_arguments}',
            pipe_std=True,
        )

    elif upload_or_download == "download":
        output = call_rclone(
            f"{rclone_args('copy')} "
            f'"{cfg.get_rclone_config_name()}:'
            f'{central_filepath}" "{local_filepath}"  {extra_arguments}',
            pipe_std=True,
        )

    return output


def get_local_and_central_file_differences(
    cfg: Configs,
    top_level_folders_to_check: List[TopLevelFolder],
) -> Dict:
    """
    Convert the output of rclone's check (with `--combine`) flag
    to a dictionary separating each case.

    Rclone output comes as a list of files, separated by newlines,
    with symbols indicating whether the file paths are same across
    local and central, different, or found in local / central only.

    Parameters
    ----------

    top_level_folders_to_check :
        List of top-level folders to check.

    Returns
    -------

    parsed_output : Dict[str, List]
        A dictionary where the keys are the cases (e.g. "same" across
        local and central) and the values are lists of paths that
        fall into these cases. Note the paths are relative to the "rawdata"
        folder.
    """
    convert_symbols = {
        "=": "same",
        "*": "different",
        "+": "local_only",
        "-": "central_only",
        "!": "error",
    }

    parsed_output: Dict[str, List]
    parsed_output = {val: [] for val in convert_symbols.values()}

    for top_level_folder in top_level_folders_to_check:

        rclone_output = perform_rclone_check(cfg, top_level_folder)  # type: ignore
        split_rclone_output = rclone_output.split("\n")

        for result in split_rclone_output:
            if result == "":
                continue

            symbol = result[0]

            assert_rclone_check_output_is_as_expected(
                result, symbol, convert_symbols
            )

            key = convert_symbols[symbol]
            parsed_output[key].append(result[2:])

    return parsed_output


def assert_rclone_check_output_is_as_expected(result, symbol, convert_symbols):
    """
    Ensure the output of Rclone check is as expected. Currently, the "error"
    case is untested and a test case is required. Once the test case is
    obtained this should most likely be moved to tests.
    """
    assert result[1] == " ", (
        "`rclone check` output does not contain a "
        "space as the second character`."
    )
    assert symbol in convert_symbols.keys(), "rclone check symbol is unknown."
    assert symbol != "!", (
        "Could not complete rlcone check. "
        "This is unexpected. Please contact datashuttle "
        "at our GitHub page."
    )


def perform_rclone_check(
    cfg: Configs, top_level_folder: TopLevelFolder
) -> str:
    """
    Use Rclone's `check` command to build a list of files that
    are the same ("="), different ("*"), found in local only ("+")
    or central only ("-"). The output is formatted as "<symbol> <path>\n".
    """
    local_filepath = cfg.get_base_folder(
        "local", top_level_folder
    ).parent.as_posix()
    central_filepath = cfg.get_base_folder(
        "central", top_level_folder
    ).parent.as_posix()

    output = call_rclone(
        f'{rclone_args("check")} '
        f'"{local_filepath}" '
        f'"{cfg.get_rclone_config_name()}:{central_filepath}"'
        f" --combined -",
        pipe_std=True,
    )

    return output.stdout.decode("utf-8")


def handle_rclone_arguments(
    rclone_options: Dict, include_list: List[str]
) -> str:
    """
    Construct the extra arguments to pass to RClone,
    """
    extra_arguments_list = []

    extra_arguments_list += ["-" + rclone_options["transfer_verbosity"]]

    overwrite = rclone_options["overwrite_existing_files"]

    if overwrite == "never":
        extra_arguments_list += [rclone_args("never_overwrite")]

    elif overwrite == "always":
        pass

    elif overwrite == "if_source_newer":
        extra_arguments_list += [rclone_args("if_source_newer_overwrite")]

    if rclone_options["show_transfer_progress"]:
        extra_arguments_list += [rclone_args("progress")]

    if rclone_options["dry_run"]:
        extra_arguments_list += [rclone_args("dry_run")]

    extra_arguments_list += include_list

    extra_arguments = " ".join(extra_arguments_list)

    return extra_arguments


def rclone_args(name: str) -> str:
    """
    Central function to hold rclone commands
    """
    valid_names = [
        "dry_run",
        "copy",
        "never_overwrite",
        "if_source_newer_overwrite",
        "progress",
        "check",
    ]
    assert name in valid_names, f"`name` must be in: {valid_names}"

    if name == "dry_run":
        arg = "--dry-run"

    if name == "copy":
        arg = "copy"

    if name == "never_overwrite":
        arg = "--ignore-existing"

    if name == "if_source_newer_overwrite":
        arg = "--update"

    if name == "progress":
        arg = "--progress"

    if name == "check":
        arg = "check"

    return arg
