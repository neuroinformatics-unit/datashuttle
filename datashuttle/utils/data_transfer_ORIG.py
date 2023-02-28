import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union

from datashuttle.configs import canonical_directories
from datashuttle.configs.configs import Configs

from . import directories, formatting, rclone, utils

# --------------------------------------------------------------------------------------------------------------------
# File Transfer
# --------------------------------------------------------------------------------------------------------------------


def transfer_sub_ses_data(
    cfg: Configs,
    upload_or_download: str,
    sub_names: Union[str, List[str]],
    ses_names: Union[str, List[str]],
    data_type: str,
    dry_run: bool,
    log: bool = True,
) -> None:
    """
    Iterate through all data type, sub, ses and transfer directory.

    At each level, transfer either the data-type directories, or
    all non-data-type directories, depending on the passed arguments.

    Parameters
    ----------

    cfg : Datshuttle Configs class

    upload_or_download : "upload" or "download"

    sub_names : see make_sub_dir()

    ses_names : see make_sub_dir()

    data_type : e.g. ephys, behav, histology, funcimg, see make_sub_dir()

    dry_run : see upload_project_dir_or_file()

    log : bool to log or not
    """
    (
        sub_names_checked,
        ses_names_checked,
        data_type_checked,
    ) = check_transfer_sub_ses_input(sub_names, ses_names, data_type)

    local_or_remote = "local" if upload_or_download == "upload" else "remote"
    base_dir = cfg.get_base_dir(local_or_remote)

    # Find sub names to transfer
    processed_sub_names = get_processed_names(
        cfg, local_or_remote, base_dir, sub_names_checked
    )

    for sub in processed_sub_names:

        if sub == "all_non_sub":

            transfer_all_non_sub_ses_data_type(
                cfg,
                upload_or_download,
                local_or_remote,
                None,
                None,
                dry_run,
                log,
            )
            continue

        transfer_data_type(
            cfg,
            upload_or_download,
            local_or_remote,
            data_type_checked,
            sub,
            dry_run=dry_run,
            log=log,
        )

        # Find ses names  to transfer
        processed_ses_names = get_processed_names(
            cfg, local_or_remote, base_dir, ses_names_checked, sub
        )

        for ses in processed_ses_names:

            if ses == "all_non_ses":
                transfer_all_non_sub_ses_data_type(
                    cfg,
                    upload_or_download,
                    local_or_remote,
                    sub,
                    None,
                    dry_run,
                    log,
                )
                continue

            if transfer_non_data_type(data_type_checked):

                transfer_all_non_sub_ses_data_type(
                    cfg,
                    upload_or_download,
                    local_or_remote,
                    sub,
                    ses,
                    dry_run,
                    log,
                )

            transfer_data_type(
                cfg,
                upload_or_download,
                local_or_remote,
                data_type_checked,
                sub,
                ses,
                dry_run=dry_run,
                log=log,
            )


def get_processed_names(
    cfg: Configs,
    local_or_remote: str,
    base_dir: Path,
    names_checked: List[str],
    sub: Optional[str] = None,
):
    """
    Process the list of subject session names.
    If they are pre-defined (e.g. ["sub-001", "sub-002"])
    they will be checked and formatted as per
    formatting.check_and_format_names() and
    any wildcard entries searched.

    Otherwise, if "all" or a variant, the local or
    remote directory (depending on upload vs. download)
    will be searched to determine what files exist to transfer,
    and the sub / ses names list generated.

    Parameters
    ----------

    see transfer_sub_ses_data()

    """
    if sub is None:
        sub_or_ses = "sub"
        search_prefix = cfg.sub_prefix
    else:
        sub_or_ses = "ses"
        search_prefix = cfg.ses_prefix

    if names_checked in [["all"], [f"all_{sub_or_ses}"]]:
        processed_names = directories.search_sub_or_ses_level(
            cfg, base_dir, local_or_remote, sub, search_str=f"{search_prefix}*"
        )[0]
        if names_checked == ["all"]:
            processed_names += [f"all_non_{sub_or_ses}"]

    else:
        processed_names = formatting.check_and_format_names(
            cfg, names_checked, sub_or_ses
        )
        processed_names = directories.search_for_wildcards(
            cfg, base_dir, local_or_remote, processed_names, sub=sub
        )

    return processed_names


def transfer_data_type(
    cfg: Configs,
    upload_or_download: str,
    local_or_remote: str,
    data_type: List[str],
    sub: str,
    ses: Optional[str] = None,
    dry_run: bool = False,
    log: bool = False,
) -> None:
    """
    Transfer the data_type-level folder at the subject
    or session level. data_type dirs are got either
    directly from user input or if "all" is passed searched
    for in the local / remote directory (for
    upload / download respectively).

    This can handle both cases of subject level dir (e.g. histology)
    or session level dir (e.g. ephys).

    Note that the use of upload_or_download / local_or_remote
    is redundant as the value of local_or_remote is set by
    upload_or_download, but kept for readability.

    Parameters
    ----------

    upload_or_download : "upload" or "download"

    local_or_remote : "local" or "remote"

    data_type : e.g. "behav", "all"

    sub : subject name

    ses : Optional session name. If False, directory
        to transfer will be assumed to be at the
        subject level.

    dry_run : Show data transfer output but do not
        actually transfer the data.

    log : Whether to log, if True logging must already
        be initialized
    """
    data_type = list(
        filter(lambda x: x != "all_ses_level_non_data_type", data_type)
    )

    data_type_items = cfg.items_from_data_type_input(
        local_or_remote, data_type, sub, ses
    )

    level = "ses" if ses else "sub"

    for data_type_key, data_type_dir in data_type_items:  # type: ignore

        if data_type_dir.level == level:
            if ses:
                filepath = os.path.join(sub, ses, data_type_dir.name)
            else:
                filepath = os.path.join(sub, data_type_dir.name)

            move_dir_or_file(
                filepath,
                cfg,
                upload_or_download,
                dry_run=dry_run,
                log=log,
            )


def transfer_all_non_sub_ses_data_type(
    cfg: Configs,
    upload_or_download: str,
    local_or_remote: str,
    sub: Optional[str],
    ses: Optional[str],
    dry_run: bool,
    log: bool,
):
    """
    Transfer all files and folders that are not included
    in the 'canonical' subject, session or data_type
    directories (e.g. behav, ephys).

    There are three possible levels, the top level, where
    anything that is not a subject is transferred (all_non_sub),
    the subject level, where anything that is not a session
    (all_non_ses), and the session level,
    where anything that is not a data-type is transferred.

    The level is determined by whether sub or session is passed.
    If neither is passed,The top-level is assumed. If subject but
    not session is passed, the subject level is assumed. If both
    subject and session are passed, the session level is assumed.

    Parameters
    ----------

    see transfer_data_type()
    """
    data_type_dirs = canonical_directories.get_data_type_directories(cfg)
    data_type_names = [dir.name for dir in data_type_dirs.values()]

    if not sub and not ses:  # i.e. "all_non_sub":

        relative_path = ""

        sub_names = directories.search_sub_or_ses_level(
            cfg,
            cfg.get_base_dir(local_or_remote),
            local_or_remote,
            search_str=f"{cfg.sub_prefix}*",
        )[0]
        exclude_list = sub_names

    elif sub and not ses:  # i.e. "all_non_ses":

        relative_path = sub

        ses_names = directories.search_sub_or_ses_level(
            cfg,
            cfg.get_base_dir(local_or_remote) / relative_path,
            local_or_remote,
            search_str=f"{cfg.ses_prefix}*",
        )[0]

        exclude_list = ses_names + data_type_names

    elif sub and ses:  # i.e. "all_ses_level_non_data_type":

        relative_path = "/".join([sub, ses])

        exclude_list = data_type_names

    move_dir_or_file(
        relative_path,
        cfg,
        upload_or_download=upload_or_download,
        dry_run=dry_run,
        log=log,
        exclude_list=exclude_list,
    )


def move_dir_or_file(
    filepath,
    cfg,
    upload_or_download: str,
    dry_run: bool,
    log: bool = False,
    exclude_list=None,
) -> None:
    """
    Low-level function to transfer a directory or file.

    Parameters
    ----------

    filepath : filepath (not including local
        or remote root) to copy

    upload_or_download : "upload" or "download".
        upload goes local to remote, download goes
        remote to local

    dry_run : do not actually move the files,
        just report what would be moved.
    """
    local_filepath = cfg.make_path("local", filepath).as_posix()
    remote_filepath = cfg.make_path("remote", filepath).as_posix()

    output = transfer_data(
        local_filepath,
        remote_filepath,
        cfg.get_rclone_config_name(),
        upload_or_download,
        exclude_list,
        cfg.make_rclone_transfer_options(dry_run),
    )

    if log:
        utils.log(output.stderr.decode("utf-8"))
    utils.message_user(output.stderr.decode("utf-8"))


def check_transfer_sub_ses_input(
    sub_names: Union[str, List[str]],
    ses_names: Union[str, List[str]],
    data_type: Union[str, List[str]],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Check the sub / session names passed. The checking here
    is stricter than for make_sub_dirs / formatting.check_and_format_names
    because we want to ensure that a) non-data-type arguments are not
    passed at the wrong input (e.g. all_non_ses as a subject name).

    We also want to limit the possible combinations of inputs, such
    that is a user inputs "all" subjects,  or "all_sub", they should
    not also pass specific subs (e.g. "sub-001"). However, all_non_sub
    and sub-001 would be permitted.

    Parameters
    ----------

    see transfer_data_type()
    """
    if isinstance(sub_names, str):
        sub_names = [sub_names]

    if isinstance(ses_names, str):
        ses_names = [ses_names]

    if isinstance(data_type, str):
        data_type = [data_type]

    if len(sub_names) > 1 and any(
        [name in ["all", "all_sub"] for name in sub_names]
    ):
        utils.log_and_raise_error(
            "sub_names must only include 'all' or 'all_subs' if these options are used"
        )  # TODO: if you pass something that doesn't exist, there is no warning

    if len(ses_names) > 1 and any(
        [name in ["all", "all_ses"] for name in ses_names]
    ):
        utils.log_and_raise_error(
            "ses_names must only include 'all' or 'all_ses' if these options are used"
        )

    if len(data_type) > 1 and any(
        [name in ["all", "all_data_type"] for name in data_type]
    ):
        utils.log_and_raise_error(
            "data_type must only include 'all' or 'all_data_type' if these options are used"
        )

    return sub_names, ses_names, data_type


def transfer_non_data_type(data_type_checked: List[str]) -> bool:
    """
    Convenience function, bool if all non-data-type directories
    are to be transferred
    """
    return any(
        [
            name in ["all_ses_level_non_data_type", "all"]
            for name in data_type_checked
        ]
    )


def transfer_data(
    local_filepath: str,
    remote_filepath: str,
    rclone_config_name: str,
    upload_or_download: str,
    exclude_list: list,
    rclone_options: dict,
) -> subprocess.CompletedProcess:
    """
    Call Rclone copy command with appropriate
    arguments to execute data transfer.

    Parameters
    ----------

    local_filepath : path to the local directory to
        transfer / be transferred to

    remote_filepath : path to the remote directory to
        transfer / be transferred to

    rclone_config_name : name of the rclone config that
        includes information on the target filesystem (e.g.
        ssh login details). This is managed by datashuttle
        e.g. setup_remote_as_rclone_target()

    upload_or_download : "upload" or "download" dictates
        direction of file transfer

    dry_run : if True, output will be as usual but no
        file will be transferred.
    """
    extra_arguments = handle_rclone_arguments(rclone_options, exclude_list)

    if upload_or_download == "upload":

        output = rclone.call_rclone(
            f"{rclone.rclone_args('copy')} "
            f'"{local_filepath}" "{rclone_config_name}:{remote_filepath}" {extra_arguments}',
            pipe_std=True,
        )

    elif upload_or_download == "download":

        output = rclone.call_rclone(
            f"{rclone.rclone_args('copy')} "
            f'"{rclone_config_name}:'
            f'{remote_filepath}" '
            f'"{local_filepath}"  '
            f"{extra_arguments}",
            pipe_std=True,
        )

    return output


def handle_rclone_arguments(rclone_options, exclude_list):
    """
    Construct the extra arguments to pass to RClone based on the
    current configs.
    """
    extra_arguments_list = [rclone.rclone_args("create_empty_src_dirs")]

    extra_arguments_list += ["-" + rclone_options["transfer_verbosity"]]

    if not rclone_options["overwrite_old_files"]:
        extra_arguments_list += [rclone.rclone_args("ignore_existing")]

    if rclone_options["show_transfer_progress"]:
        extra_arguments_list += [rclone.rclone_args("progress")]

    if rclone_options["dry_run"]:
        extra_arguments_list += [rclone.rclone_args("dry_run")]

    if exclude_list:
        exclude_text = " --exclude "
        full_exclude_paths = [path_ + "/**" for path_ in exclude_list]
        exclude_flags = (
            f"{exclude_text}{exclude_text.join(full_exclude_paths)}"
        )
        extra_arguments_list += [exclude_flags]

    extra_arguments = " ".join(extra_arguments_list)

    return extra_arguments
