"""
Explain. Explain why it is horrible.
"""
from pathlib import Path
from typing import List, Optional

from datashuttle.configs import canonical_directories, configs

from . import directories, rclone, utils


def transfer_all_non_sub_ses_data_type(
    cfg: configs.Configs,
    upload_or_download: str,
    local_or_remote: str,
    type_: str,
    sub: str,
    ses: str,
    dry_run: bool,
    log: bool,
):
    """"""
    data_type_dirs = canonical_directories.get_data_type_directories(cfg)
    data_type_names = [dir.name for dir in data_type_dirs.values()]

    if type_ == "all_non_sub":

        relative_path = ""

        sub_names = directories.search_sub_or_ses_level(
            cfg,
            cfg.get_base_dir(local_or_remote),
            local_or_remote,
            search_str=f"{cfg.sub_prefix}*",
        )
        exclude_list = sub_names

    elif type_ == "all_non_ses":

        relative_path = sub

        ses_names = directories.search_sub_or_ses_level(
            cfg,
            cfg.get_base_dir(local_or_remote) / relative_path,
            local_or_remote,
            search_str=f"{cfg.ses_prefix}*",
        )

        exclude_list = ses_names + data_type_names

    elif type_ == "all_ses_level_non_data_type":

        relative_path = sub + "/" + "/" + ses

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
    exclude_list: Optional[List[str]] = None,
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

    output = rclone.transfer_data(
        local_filepath,
        remote_filepath,
        cfg.get_rclone_config_name(),
        upload_or_download,
        rclone_options=cfg.make_rclone_transfer_options(dry_run, exclude_list),
    )

    if log:
        utils.log(output.stderr.decode("utf-8"))
    utils.message_user(output.stderr.decode("utf-8"))
