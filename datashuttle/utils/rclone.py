from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Literal, Optional

if TYPE_CHECKING:
    from datashuttle.configs.config_class import Configs
    from datashuttle.utils.custom_types import TopLevelFolder

import os
import platform
import shlex
import subprocess
import tempfile
from pathlib import Path
from subprocess import CompletedProcess

from datashuttle.configs import canonical_configs
from datashuttle.utils import rclone_password, utils


def call_rclone(command: str, pipe_std: bool = False) -> CompletedProcess:
    """Call rclone with the specified command.

    Parameters
    ----------
    command
        Rclone command to be run

    pipe_std
        if True, do not output anything to stdout.

    Returns
    -------
    subprocess.CompletedProcess with `stdout` and `stderr` attributes.

    """
    command = "rclone " + command
    if pipe_std:
        output = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
    else:
        output = subprocess.run(command, shell=True)

    if output.returncode != 0:
        prompt_rclone_download_if_does_not_exist()

    return output


def call_rclone_for_central_connection(
    cfg, command: str, pipe_std: bool = False
) -> CompletedProcess:
    return run_function_that_may_require_central_connection_password(
        cfg, lambda: call_rclone(command, pipe_std)
    )


def call_rclone_through_script_for_central_connection(
    cfg, command: str
) -> CompletedProcess:
    """Call rclone through a script.

    This is to avoid limits on command-line calls (in particular on Windows).
    Used for transfers due to generation of large call strings.

    Parameters
    ----------
    command
        Full command to run with RClone.

    Returns
    -------
    subprocess.CompletedProcess with `stdout` and `stderr` attributes.

    """
    system = platform.system()

    command = "rclone " + command

    if system == "Windows":
        suffix = ".bat"
    else:
        suffix = ".sh"
        command = "#!/bin/bash\n" + command

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False
    ) as tmp_script:
        tmp_script.write(command)
        tmp_script_path = tmp_script.name

    try:
        if system != "Windows":
            os.chmod(tmp_script_path, 0o700)

        lambda_func = lambda: subprocess.run(
            [tmp_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        output = run_function_that_may_require_central_connection_password(
            cfg, lambda_func
        )

        if output.returncode != 0:
            prompt_rclone_download_if_does_not_exist()

    finally:
        os.remove(tmp_script_path)

    return output


def call_rclone_with_popen_for_central_connection(
    cfg,
    command: str,
) -> subprocess.Popen:
    """Call rclone using `subprocess.Popen` for control over process termination.

    It is not possible to kill a process while running it using `subprocess.run`.
    Killing a process might be required when running rclone setup in a thread worker
    to allow the user to cancel the setup process. In such a case, cancelling the
    thread worker alone will not kill the rclone process, so we need to kill the
    process explicitly.
    """
    command = "rclone " + command
    lambda_func = lambda: subprocess.Popen(
        shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    process = run_function_that_may_require_central_connection_password(
        cfg, lambda_func
    )
    return process


def await_call_rclone_with_popen_for_central_connection_raise_on_fail(
    cfg, process: subprocess.Popen, log: bool = True
):
    """Await rclone the subprocess.Popen call.

    Calling `process.communicate()` waits for the process to complete and returns
    the stdout and stderr.
    """
    lambda_func = lambda: process.communicate()

    stdout, stderr = run_function_that_may_require_central_connection_password(
        cfg, lambda_func
    )

    if process.returncode != 0:
        utils.log_and_raise_error(stderr.decode("utf-8"), ConnectionError)

    if log:
        log_rclone_config_output()


def run_function_that_may_require_central_connection_password(
    cfg, lambda_func
):
    """ """
    set_password = cfg.rclone_has_password[cfg["connection_method"]]

    if set_password:
        config_filepath = rclone_password.get_password_filepath(cfg)
        rclone_password.set_credentials_as_password_command(config_filepath)

    results = lambda_func()

    if set_password:
        rclone_password.remove_credentials_as_password_command()

    return results


# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------


def setup_rclone_config_for_local_filesystem(
    rclone_config_name: str,
    log: bool = True,
) -> None:
    """Set the RClone remote config for local filesystem.

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
    rclone_config_name
        canonical config name, generated by
        datashuttle.cfg.get_rclone_config_name()

    log
        whether to log, if True logger must already be initialised.

    """
    call_rclone(f"config create {rclone_config_name} local", pipe_std=True)

    if log:
        log_rclone_config_output()


def setup_rclone_config_for_ssh(
    cfg: Configs,
    rclone_config_name: str,
    private_key_str: str,
    log: bool = True,
) -> None:
    """Set the RClone remote config for ssh.

    RClone sets remote targets in a config file that are
    used at transfer. For SSH, this must contain the central path,
    username and ssh key. The relative path is supplied at transfer time.

    Parameters
    ----------
    cfg
        datashuttle configs UserDict.

    rclone_config_name
        canonical config name, generated by
        datashuttle.cfg.get_rclone_config_name()

    private_key_str
        PEM encoded ssh private key to pass to RClone.

    log
        whether to log, if True logger must already be initialised.

    """
    key_escaped = private_key_str.replace("\n", "\\n")

    rclone_config_filepath = get_full_config_filepath(
        cfg
    )  # TODO: do this for everything TODO: maybe this config file can be created before setup in case of old file
    if rclone_config_filepath.exists():
        rclone_config_filepath.unlink()

    command = (
        f"config create "
        f"{rclone_config_name} "
        f"sftp "
        f"host {cfg['central_host_id']} "
        f"user {cfg['central_host_username']} "
        f"port {canonical_configs.get_default_ssh_port()} "
        f"{get_config_arg(cfg)} "
        f'-- key_pem "{key_escaped}"'
    )
    call_rclone(command, pipe_std=True)

    if log:
        log_rclone_config_output()


def get_config_path():
    """TODO PLACEHOLDER."""
    return (
        Path().home() / "AppData" / "Roaming" / "rclone"
    )  #  # "$HOME/.config/rclone/rclone.conf")


def get_full_config_filepath(cfg: Configs) -> Path:
    return get_config_path() / f"{cfg.get_rclone_config_name()}.conf"


def get_config_arg(cfg):
    """TODO PLACEHOLDER."""
    cfg.get_rclone_config_name()  # pass this? handle better...

    if cfg["connection_method"] in ["aws", "gdrive", "ssh"]:
        return f'--config "{get_full_config_filepath(cfg)}"'
    else:
        return ""


def set_password(cfg, password: str):
    subprocess.run(
        f"rclone config encryption set {get_config_arg(cfg)}", text=True
    )


# def remove_password():


def setup_rclone_config_for_gdrive(
    cfg: Configs,
    rclone_config_name: str,
    gdrive_client_secret: str | None,
    config_token: Optional[str] = None,
) -> subprocess.Popen:
    """Set up rclone config for connections to Google Drive.

    This function uses `call_rclone_with_popen_for_central_connection` instead of `call_rclone`. This
    is done to have more control over the setup process in case the user wishes to
    cancel the setup. Since the rclone setup for google drive uses a local web server
    for authentication to google drive, the running process must be killed before the
    setup can be started again.

    Parameters
    ----------
    cfg
       datashuttle configs UserDict. This must contain the `gdrive_root_folder_id`
       and optionally a `gdrive_client_id` which also mandates for the presence
       of a Google Drive client secret.

    rclone_config_name
         Canonical config name, generated by
         datashuttle.cfg.get_rclone_config_name()

    gdrive_client_secret
        Google Drive client secret, mandatory when using a Google Drive client.

    config_token : a token to setup rclone config without opening a browser,
        needed if the user's machine doesn't have access to a browser.

    """
    client_id_key_value = (
        f"client_id {cfg['gdrive_client_id']} "
        if cfg["gdrive_client_id"]
        else " "
    )
    client_secret_key_value = (
        f"client_secret {gdrive_client_secret} "
        if gdrive_client_secret
        else ""
    )

    extra_args = (
        f"config_is_local=false config_token={config_token}"
        if config_token
        else ""
    )

    process = call_rclone_with_popen_for_central_connection(
        cfg,
        f"config create "
        f"{rclone_config_name} "
        f"drive "
        f"{client_id_key_value}"
        f"{client_secret_key_value}"
        f"scope drive "
        f"root_folder_id {cfg['gdrive_root_folder_id']} "
        f"{extra_args} "
        f"{get_config_arg(cfg)}",
    )

    return process


def setup_rclone_config_for_aws(
    cfg: Configs,
    rclone_config_name: str,
    aws_secret_access_key: str,
    log: bool = True,
):
    """Set up rclone config for connections to AWS S3 buckets.

    Parameters
    ----------
    cfg
       datashuttle configs UserDict.
       Must contain the `aws_access_key_id` and `aws_region`.

    rclone_config_name
        Canonical RClone config name, generated by
        datashuttle.cfg.get_rclone_config_name()

    aws_secret_access_key
        The aws secret access key provided by the user.

    log
        Whether to log, if True logger must already be initialised.

    """
    aws_region = cfg["aws_region"]

    # Rclone mandates location_constraint be set as the aws regions for
    # all regions except us-east-1
    location_constraint_key_value = (
        ""
        if aws_region == "us-east-1"
        else f" location_constraint {aws_region}"
    )

    output = call_rclone(
        "config create "
        f"{rclone_config_name} "
        "s3 provider AWS "
        f"access_key_id {cfg['aws_access_key_id']} "
        f"secret_access_key {aws_secret_access_key} "
        f"region {aws_region}"
        f"{location_constraint_key_value} "
        f"{get_config_arg(cfg)}",
        pipe_std=True,
    )

    if output.returncode != 0:
        utils.log_and_raise_error(
            output.stderr.decode("utf-8"), ConnectionError
        )

    if log:
        log_rclone_config_output()


def check_successful_connection_and_raise_error_on_fail(cfg: Configs) -> None:
    """Check for a successful connection by creating a file on the remote.

    If the command fails, it raises a ConnectionError. The created file is
    deleted thereafter.
    """
    filename = f"{utils.get_random_string()}_temp.txt"

    if cfg["central_path"] is None:
        assert cfg["connection_method"] == "gdrive", (
            "`central_path` may only be `None` for `gdrive`"
        )
        tempfile_path = filename
    else:
        tempfile_path = (cfg["central_path"] / filename).as_posix()

    config_name = cfg.get_rclone_config_name()

    output = call_rclone_for_central_connection(
        cfg,
        f"touch {config_name}:{tempfile_path} {get_config_arg(cfg)}",
        pipe_std=True,
    )
    if output.returncode != 0:
        utils.log_and_raise_error(
            output.stderr.decode("utf-8"), ConnectionError
        )

    output = call_rclone_for_central_connection(
        cfg,
        f"delete {cfg.get_rclone_config_name()}:{tempfile_path} {get_config_arg(cfg)}",
        pipe_std=True,
    )
    if output.returncode != 0:
        utils.log_and_raise_error(
            output.stderr.decode("utf-8"), ConnectionError
        )


def log_rclone_config_output() -> None:  # TODO: remove or update this
    """Log the output from creating Rclone config."""
    output = call_rclone("config file", pipe_std=True)
    utils.log(
        f"Successfully created rclone config. {output.stdout.decode('utf-8')}"
    )


def prompt_rclone_download_if_does_not_exist() -> None:
    """Check that rclone is installed."""
    if not check_rclone_with_default_call():
        newline = "" if "PYTEST_CURRENT_TEST" in os.environ else "\n"

        utils.log_and_raise_error(
            f"RClone installation not found. Install by entering "
            f"the following into your terminal:{newline}"
            f"  conda install -c conda-forge rclone",
            RuntimeError,
        )


def check_rclone_with_default_call() -> bool:
    """Return a bool indicating whether rclone is installed.

    Must not use `call_rclone` or leads to recursion.
    """
    try:
        output = subprocess.run(
            "rclone -h",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
    except FileNotFoundError:
        return False
    return True if output.returncode == 0 else False


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
    """Transfer data by making a call to Rclone.

    Parameters
    ----------
    cfg
        datashuttle configs

    upload_or_download
        If "upload", transfer from `local_path` to `central_path`.
        "download" proceeds in the opposite direction.

    top_level_folder
        The top-level-folder to transfer files within.

    include_list
        A list of filepaths to include in the transfer

    rclone_options
        A list of options to pass to Rclone's copy function.
        see `cfg.make_rclone_transfer_options()`.

    Returns
    -------
    subprocess.CompletedProcess with `stdout` and `stderr` attributes.

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

    #    if cfg.rclone_has_password[cfg["connection_method"]]:  # TODO: one getter
    #        print("SET")
    #        config_filepath = rclone_password.get_password_filepath(
    #            cfg
    #        )  # TODO: ONE FUNCTION OR INCORPORATE INTO SINGLE FUNCTION
    #        rclone_password.set_credentials_as_password_command(config_filepath)

    if upload_or_download == "upload":
        output = call_rclone_through_script_for_central_connection(
            cfg,
            f"{rclone_args('copy')} "
            f'"{local_filepath}" "{cfg.get_rclone_config_name()}:'
            f'{central_filepath}" {extra_arguments} {get_config_arg(cfg)} --ask-password=false',  # TODO: handle the error
        )

    elif upload_or_download == "download":
        output = call_rclone_through_script_for_central_connection(
            cfg,
            f"{rclone_args('copy')} "
            f'"{cfg.get_rclone_config_name()}:'
            f'{central_filepath}" "{local_filepath}"  {extra_arguments} {get_config_arg(cfg)} --ask-password=false',  # TODO: handle the error
        )

    if cfg.rclone_has_password[cfg["connection_method"]]:
        print("REMOVED")
        rclone_password.remove_credentials_as_password_command()

    return output


def get_local_and_central_file_differences(
    cfg: Configs,
    top_level_folders_to_check: List[TopLevelFolder],
) -> Dict:
    """Format a structure of all changes between local and central.

    Rclone output comes as a list of files, separated by newlines,
    with symbols indicating whether the file paths are same across
    local and central, different, or found in local / central only.

    Convert the output of Rclone's check (with `--combine`) flag
    to a dictionary separating each case.

    Parameters
    ----------
    cfg
        datashuttle configs UserDict.

    top_level_folders_to_check
        List of top-level folders to check.

    Returns
    -------
    parsed_output
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
    """Ensure the output of Rclone check is as expected.

    Currently, the "error" case is untested and a test case is required.
    Once the test case is obtained this should most likely be moved to tests.
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
    r"""Run RClone check to find differences in files between local and central.

    Use Rclone's `check` command to build a list of files that
    are the same ("="), different ("*"), found in local only ("+")
    or central only ("-"). The output is formatted as "\<symbol> \<path>\n".
    """
    local_filepath = cfg.get_base_folder(
        "local", top_level_folder
    ).parent.as_posix()
    central_filepath = cfg.get_base_folder(
        "central", top_level_folder
    ).parent.as_posix()

    output = call_rclone_for_central_connection(
        cfg,
        f"{rclone_args('check')} "
        f'"{local_filepath}" '
        f'"{cfg.get_rclone_config_name()}:{central_filepath}"'
        f"{get_config_arg(cfg)} "
        f"--combined -",
        pipe_std=True,
    )

    return output.stdout.decode("utf-8")


def handle_rclone_arguments(
    rclone_options: Dict, include_list: List[str]
) -> str:
    """Construct the extra arguments to pass to RClone.

    Parameters
    ----------
    rclone_options
        A list of option keywords to be passed to

    include_list
        The (already formatted) list of filepaths for the
        rclone `--include` option.

    Returns
    -------
    A full list of arguments to pass to rclone.

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
    """Return list of Rclone commands."""
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
