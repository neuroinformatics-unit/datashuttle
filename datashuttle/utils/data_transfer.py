from pathlib import Path
from typing import List, Optional

from . import rclone, utils


def _transfer_all_non_sub_ses_data_type_(
    self,
    upload_or_download,
    local_or_remote,
    type_,
    sub,
    ses,
    dry_run,
    log,
):  # TODO: add typing!!, make sub and ses optional
    """"""
    data_type_names = [
        dir.name
        for dir in canonical_directories.get_data_type_directories(
            self.cfg
        ).values()
    ]

    if type_ == "all_non_sub":  # TODO type is builtin!

        relative_path = ""  # TODO!!!

        sub_names = directories.search_sub_or_ses_level(
            self,
            self.cfg.get_base_dir(local_or_remote),
            local_or_remote,
            search_str=f"{self.cfg.sub_prefix}*",
        )

        exclude_list = sub_names

    elif type_ == "all_non_ses":

        relative_path = sub

        ses_names = directories.search_sub_or_ses_level(
            self,
            self.cfg.get_base_dir(local_or_remote) / relative_path,
            local_or_remote,
            search_str=f"{self.cfg.ses_prefix}*",
        )  # TODO: this is not clean

        exclude_list = ses_names + data_type_names

    elif type_ == "all_ses_level_non_data_type":

        relative_path = sub + "/" + "/" + ses  # TODO fix

        exclude_list = data_type_names

    data_transfer.move_dir_or_file(
        relative_path,
        self.cfg,
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
