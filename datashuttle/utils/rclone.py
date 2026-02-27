from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    TypeVar,
)

T = TypeVar("T")

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess

    from datashuttle.configs.config_class import Configs
    from datashuttle.utils.custom_types import (
        OverwriteExistingFiles,
        TopLevelFolder,
    )

import json
import os
import platform
import shlex
import subprocess
import tempfile
from pathlib import Path
from subprocess import CompletedProcess

from datashuttle.configs import canonical_configs
from datashuttle.utils import rclone_encryption, utils
from datashuttle.utils.transfer_output_class import TransferOutput


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
    """Call RClone when the config file may need to be decrypted.

    This is a convenience function to call RClone in places where
    the config file may need to be decrypted. This is for connecting
    to the central storage through aws, ssh or gdrive. It wraps the
    function call in a set-up / teardown of the config password.
    """
    return run_function_that_requires_encrypted_rclone_config_access(
        cfg, lambda: call_rclone(command, pipe_std)
    )


def call_rclone_through_script_for_central_connection(
    cfg: Configs, command: str
) -> CompletedProcess:
    """Call rclone through a script.

    This is to avoid limits on command-line calls (in particular on Windows).
    Used for transfers due to generation of large call strings.

    Parameters
    ----------
    cfg
        Datashuttle Configs class.
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

        if rclone_encryption.connection_method_requires_encryption(
            cfg["connection_method"]
        ):
            output = run_function_that_requires_encrypted_rclone_config_access(
                cfg, lambda_func
            )
        else:
            output = lambda_func()

        if output.returncode != 0:
            prompt_rclone_download_if_does_not_exist()

    finally:
        os.remove(tmp_script_path)

    return output


def call_rclone_with_popen(
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

    # this command must use shell=False (and thus shlex.split) otherwise
    # the process cannot be properly cancelled.
    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def await_call_rclone_with_popen_for_central_connection_raise_on_fail(
    cfg: Configs, process: subprocess.Popen, log: bool = True
):
    """Await rclone the subprocess.Popen call.

    Calling `process.communicate()` waits for the process to complete and returns
    the stdout and stderr.
    """
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        utils.log_and_raise_error(stderr.decode("utf-8"), ConnectionError)

    if log:
        log_rclone_config_output(cfg)

    return stdout, stderr


def run_function_that_requires_encrypted_rclone_config_access(
    cfg: Configs,
    lambda_func: Callable[..., T],
    check_config_exists: bool = True,
) -> T:
    """Run command that requires possibly encrypted Rclone config file.

    The Rclone config file may be encrypted for aws, gdrive or ssh connections.
    In this case we need to set an environment variable to tell Rclone how
    to decrypt the config file (and remove the variable afterwards).
    """
    rclone_config_filepath = (
        cfg.rclone.get_rclone_central_connection_config_filepath()
    )

    if check_config_exists and not rclone_config_filepath.is_file():
        raise RuntimeError(
            f"The Rclone config file cannot be found. You may be seeing this as the way "
            f"Rclone configs are managed was changed in v0.7.1\n"
            f"Please set up the {cfg['connection_method']} connection again."
        )

    is_encrypted = cfg.rclone.rclone_file_is_encrypted()

    if is_encrypted:
        rclone_encryption.set_credentials_as_password_command(cfg)

    try:
        results = lambda_func()
    finally:
        if is_encrypted:
            rclone_encryption.remove_rclone_password_env_var()

    return results


# -----------------------------------------------------------------------------
# RClone Configs
# -----------------------------------------------------------------------------


def setup_rclone_config_for_local_filesystem(
    cfg: Configs,
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
    cfg
        datashuttle Configs class

    rclone_config_name
        canonical config name, generated by
        datashuttle.cfg.rclone.get_rclone_config_name()

    log
        whether to log, if True logger must already be initialised.

    """
    call_rclone(f"config create {rclone_config_name} local", pipe_std=True)

    if log:
        log_rclone_config_output(cfg)


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
        datashuttle.cfg.rclone.get_rclone_config_name()

    private_key_str
        PEM encoded ssh private key to pass to RClone.

    log
        whether to log, if True logger must already be initialised.

    """
    key_escaped = private_key_str.replace("\n", "\\n")

    cfg.rclone.delete_existing_rclone_config_file()

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
        log_rclone_config_output(cfg)


def setup_rclone_config_for_gdrive(
    cfg: Configs,
    rclone_config_name: str,
    gdrive_client_secret: str | None,
    config_token: Optional[str] = None,
) -> subprocess.Popen:
    """Set up rclone config for connections to Google Drive.

    This function uses `call_rclone_with_popen` instead of `call_rclone`. This
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
         datashuttle.cfg.rclone.get_rclone_config_name()

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

    cfg.rclone.delete_existing_rclone_config_file()

    command = (
        f"config create "
        f"{rclone_config_name} "
        f"drive "
        f"{client_id_key_value}"
        f"{client_secret_key_value}"
        f"scope drive "
        f"root_folder_id {cfg['gdrive_root_folder_id']} "
        f"{extra_args} "
        f"{get_config_arg(cfg)}"
    )

    process = call_rclone_with_popen(command)

    return process


def preliminary_setup_gdrive_config_without_browser(
    cfg: Configs,
    gdrive_client_secret: str | None,
    rclone_config_name: str,
    log: bool = True,
) -> str:
    """Prepare rclone configuration for Google Drive without using a browser.

    This function prepares the rclone configuration for Google Drive without using a browser.

    The `config_is_local=false` flag tells rclone that the configuration process is being run
    on a headless machine which does not have access to a browser.

    The `--non-interactive` flag is used to control Rclone's behaviour while running it through
    external applications. An `rclone config create` command would assume default values for config
    variables in an interactive mode. If the `--non-interactive` flag is provided and rclone needs
    the user to input some detail, a JSON blob will be returned with the question in it. For this
    particular setup, rclone outputs a command for user to run on a machine with a browser.

    This function runs `rclone config create` with the user credentials and returns the rclone's output info.
    This output info is presented to the user while asking for a `config_token`.

    Next, the user will run rclone's given command, authenticate with google drive and input the
    config token given by rclone for datashuttle to proceed with the setup.
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

    cfg.rclone.delete_existing_rclone_config_file()

    output = call_rclone(
        f"config create "
        f"{get_config_arg(cfg)} "
        f"{rclone_config_name} "
        f"drive "
        f"{client_id_key_value}"
        f"{client_secret_key_value}"
        f"scope drive "
        f"root_folder_id {cfg['gdrive_root_folder_id']} "
        f"config_is_local=false "
        f"--non-interactive",
        pipe_std=True,
    )

    # Extracting rclone's message from the json
    output_json = json.loads(output.stdout)
    message = output_json["Option"]["Help"]

    if log:
        utils.log(message)

    return message


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
        datashuttle.cfg.rclone.get_rclone_config_name()

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

    cfg.rclone.delete_existing_rclone_config_file()

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
        log_rclone_config_output(cfg)


def get_config_arg(cfg: Configs) -> str:
    """Get the full argument to run Rclone commands with a specific config."""
    if rclone_encryption.connection_method_requires_encryption(
        cfg["connection_method"]
    ):
        rclone_config_path = (
            cfg.rclone.get_rclone_central_connection_config_filepath()
        )

        return f'--config "{rclone_config_path}"'
    else:
        return ""


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

    config_name = cfg.rclone.get_rclone_config_name()

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
        f"delete {cfg.rclone.get_rclone_config_name()}:{tempfile_path} {get_config_arg(cfg)}",
        pipe_std=True,
    )
    if output.returncode != 0:
        utils.log_and_raise_error(
            output.stderr.decode("utf-8"), ConnectionError
        )


def get_rclone_config_filepath(cfg: Configs) -> Path:
    """Get the path to the central Rclone config for the current `connection_method`."""
    if rclone_encryption.connection_method_requires_encryption(
        cfg["connection_method"]
    ):
        config_filepath = (
            cfg.rclone.get_rclone_central_connection_config_filepath()
        )
    else:
        output = call_rclone("config file", pipe_std=True)
        config_filepath = output.stdout.decode("utf-8")

    return config_filepath


def log_rclone_config_output(cfg: Configs) -> None:
    """Log the output from creating Rclone config."""
    config_filepath = get_rclone_config_filepath(cfg)
    utils.log(f"Successfully created rclone config. {config_filepath}")


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
        see `make_rclone_transfer_options()`.

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

    if upload_or_download == "upload":
        output = call_rclone_through_script_for_central_connection(
            cfg,
            f"{rclone_args('copy')} "
            f'"{local_filepath}" "{cfg.rclone.get_rclone_config_name()}:'
            f'{central_filepath}" {extra_arguments} {get_config_arg(cfg)} --use-json-log',
        )

    elif upload_or_download == "download":
        output = call_rclone_through_script_for_central_connection(
            cfg,
            f"{rclone_args('copy')} "
            f'"{cfg.rclone.get_rclone_config_name()}:'
            f'{central_filepath}" "{local_filepath}" {extra_arguments} {get_config_arg(cfg)} --use-json-log',
        )

    return output


def log_stdout_stderr_python_api(stdout: str, stderr: str) -> None:
    """Log `stdout` and `stderr`."""
    message = (
        f"\n\n**************  STDOUT  **************\n"
        f"{stdout}"
        f"\n\n**************  STDERR  **************\n"
        f"{stderr}"
    )

    utils.log_and_message(message)


def log_rclone_transfer_output(transfer_output: TransferOutput) -> None:
    """Log the `TransferOutput` dictionary.

    The `TransferOutput` dictionary contains all pertinent information on
    issues that occurred when running `rclone copy`. Note this logs
    for the API, the TUI display is handled separately.
    """
    message = transfer_output.create_python_api_message()

    utils.log_and_message(message, use_rich=True)


def parse_rclone_copy_output(
    top_level_folder: TopLevelFolder | None, output: CompletedProcess
) -> tuple[str, str, TransferOutput]:
    """Format the `rclone copy` output ready for logging.

    Reformat and combine the string streams and `TransferOutput`
    dictionary from stdout and stderr output of `rclone copy`.
    see `reformat_rclone_copy_output()` for details.
    """
    stdout, stdout_outputs = reformat_rclone_copy_output(
        output.stdout, top_level_folder=top_level_folder
    )
    stderr, stderr_outputs = reformat_rclone_copy_output(
        output.stderr, top_level_folder=top_level_folder
    )

    combined_transfer_output = TransferOutput.merge_std_outputs(
        stdout_outputs, stderr_outputs
    )

    return stdout, stderr, combined_transfer_output


def reformat_rclone_copy_output(
    stream: bytes,
    top_level_folder: TopLevelFolder | None = None,
) -> tuple[str, TransferOutput]:
    """Parse the output of `rclone copy` for convenient error checking.

    Rclone's `copy` command (called with `--use-json-log`) outputs a lot of
    information related to the transfer. We dump this in text form to a log
    file. However, we also want to grab any key events (errors, or complete
    lack of transferred files) so these can be displayed separately.

    This function iterates through all lines in the `rclone copy` output.
    This output is typically a mix of string format and json format.
    If the line is json-encoded, then we extract important information
    and format it to string, and re-insert it into the output.

    In this way, we have a string-format output ready to be
    dumped to the logs, as well as an `errors` dictionary containing
    details on all key information.

    Returns
    -------
    format_stream
        The input stream, converted to string and with all
        json-formatted lines reformatted as string. This is ready
        to be dumped to a log file.

    errors
        A dictionary (`TransferOutput`) containing key information
        about issues in the transfer.

    """
    split_stream = stream.decode("utf-8").split("\n")

    transfer_output = TransferOutput()

    for idx, line in enumerate(split_stream):
        try:
            line_json = json.loads(line)
        except json.JSONDecodeError:
            continue

        if line_json["level"] in ["error", "critical"]:
            if "object" in line_json:
                full_filepath = Path(
                    f"{top_level_folder}/{line_json['object']}"
                ).as_posix()
                transfer_output["errors"]["file_names"].append(full_filepath)
                transfer_output["errors"]["messages"].append(
                    f"The file {full_filepath} failed to transfer. Reason: {line_json['msg']}"
                )
            else:
                transfer_output["errors"]["messages"].append(
                    f"ERROR : {line_json['msg']}"
                )

        elif "stats" in line_json and "totalTransfers" in line_json["stats"]:
            transfer_output["num_transferred"][top_level_folder] = line_json[
                "stats"
            ]["totalTransfers"]

        split_stream[idx] = (
            f"{line_json['time'][:19]} {line_json['level'].upper()} : {line_json['msg']}"
        )

    format_stream = "\n".join(split_stream)

    return format_stream, transfer_output


def make_rclone_transfer_options(
    overwrite_existing_files: OverwriteExistingFiles, dry_run: bool
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


def get_local_and_central_file_differences(
    cfg: Configs,
    top_level_folders_to_check: List[TopLevelFolder],
) -> Dict[str, List]:
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

    if rclone_encryption.connection_method_requires_encryption(
        cfg["connection_method"]
    ):
        output = call_rclone_for_central_connection(
            cfg,
            f"{rclone_args('check')} "
            f'"{local_filepath}" '
            f'"{cfg.rclone.get_rclone_config_name()}:{central_filepath}" '
            f"--combined - "
            f'--exclude "*.datashuttle/logs/*" '
            f"{get_config_arg(cfg)}",
            pipe_std=True,
        )
    else:
        output = call_rclone(
            f"{rclone_args('check')} "
            f'"{local_filepath}" '
            f'"{cfg.rclone.get_rclone_config_name()}:{central_filepath}" '
            f"--combined - "
            f'--exclude "*.datashuttle/logs/*"',
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
