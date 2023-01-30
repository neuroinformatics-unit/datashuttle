def move_dir_or_file(
    local_filepath: Path,
    remote_filepath: Path,
    cfg: Configs,  # TODO:
    rclone_config_name: str,
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
    #    local_filepath = self._make_path(
    #        "local", [self._top_level_dir_name, filepath]
    #    ).as_posix()

    #    remote_filepath = self._make_path(
    #        "remote", [self._top_level_dir_name, filepath]
    #    ).as_posix()

    output = rclone.transfer_data(
        local_filepath.as_posix(),
        remote_filepath.as_posix(),
        rclone_config_name,
        upload_or_download,
        rclone_options={  # TODO: this is stupid
            "overwrite_old_files_on_transfer": cfg[
                "overwrite_old_files_on_transfer"
            ],
            "transfer_verbosity": cfg["transfer_verbosity"],
            "show_transfer_progress": cfg["show_transfer_progress"],
            "dry_run": dry_run,
            "exclude_list": exclude_list,
        },
    )

    if log:
        utils.log(output.stderr.decode("utf-8"))
    utils.message_user(output.stderr.decode("utf-8"))
