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

# fmt: on

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
    """
    sub_ses_dtype_include = []
    extra_dirnames = []
    extra_filenames = []

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
                extra_dirnames,
                extra_filenames,
                cfg,
                local_or_remote,
            )
            continue

        update_list_with_dtype_paths(
            sub_ses_dtype_include,
            cfg,
            local_or_remote,
            data_type_checked,
            sub,
        )

        # Find ses names  to transfer
        processed_ses_names = get_processed_names(
            cfg, local_or_remote, base_dir, ses_names_checked, sub
        )

        for ses in processed_ses_names:

            if ses == "all_non_ses":
                transfer_all_non_sub_ses_data_type(
                    extra_dirnames,
                    extra_filenames,
                    cfg,
                    local_or_remote,
                    sub,
                )
                continue

            if transfer_non_data_type(data_type_checked):

                transfer_all_non_sub_ses_data_type(
                    extra_dirnames,
                    extra_filenames,
                    cfg,
                    local_or_remote,
                    sub,
                    ses,
                )

            update_list_with_dtype_paths(
                sub_ses_dtype_include,
                cfg,
                local_or_remote,
                data_type_checked,
                sub,
                ses,
            )

    include_list = format_include_lists_into_rclone_args()

    if any(include_list):

        output = transfer_data(local_filepath, remote_filepath, cfg.get_rclone_config_name(), upload_or_download, include_list, cfg.make_rclone_transfer_options(dry_run))

        if log:
            utils.log(output.stderr.decode("utf-8"))
    else:
        if log:
            utils.log("No files included. None transferred.")

# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

def transfer_data(
    cfg: Configs,
    upload_or_download: str,
    include_list: list,
    rclone_options: dict,
) -> subprocess.CompletedProcess:
    """
    """
    local_filepath = cfg.get_base_dir("local").as_posix()
    remote_filepath = cfg.get_base_dir("remote").as_posix()

    extra_arguments = rclone.handle_rclone_arguments(rclone_options, include_list)  # TODO: fix this is not a list

    if upload_or_download == "upload":

        output = rclone.call_rclone(
            f"{rclone.rclone_args('copy')} "
            f'"{local_filepath}" "{cfg.get_rclone_config_name()}:{remote_filepath}" {extra_arguments}',
            pipe_std=True,
        )

    elif upload_or_download == "download":

        output = rclone.call_rclone(
            f"{rclone.rclone_args('copy')} "
            f'"{cfg.get_rclone_config_name()}:{remote_filepath}" "{local_filepath}"  {extra_arguments}',
            pipe_std=True,
        )

    return output

# -----------------------------------------------------------------------------
# Build Include Lists
# -----------------------------------------------------------------------------

def update_list_with_dtype_paths(
    sub_ses_dtype_include,
    cfg: Configs,
    local_or_remote: str,
    data_type: List[str],
    sub: str,
    ses: Optional[str] = None,
) -> None:
    """
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

            sub_ses_dtype_include.append(Path(filepath).as_posix())  # TODO: HANDLE

#    extra_dirnames,
#    extra_filenames,
def get_top_level_non_sub_paths_to_transfer(
    cfg: Configs,
    local_or_remote: str):

    top_level_dirs, top_level_files = directories.search_sub_or_ses_level(
        cfg,
        cfg.get_base_dir(local_or_remote),
        local_or_remote,
        search_str="*",
    )

    extra_dirnames += [ele for ele in top_level_dirs if ele[:4] != "sub-"]
    extra_filenames += top_level_files

def get_sub_level_extra_paths_to_transfer(
    cfg: Configs,
    local_or_remote: str,
    sub: Optional[str] = None,):


def get_ses_level_extra_paths_to_transfer():

def transfer_all_non_sub_ses_data_type(
    extra_dirnames,
    extra_filenames,
    cfg: Configs,
    local_or_remote: str,
    sub: Optional[str] = None,
    ses: Optional[str] = None,
):
    """
    """
    if not sub and not ses:  # i.e. "all_non_sub":

        top_level_dirs, top_level_files = directories.search_sub_or_ses_level(
            cfg,
            cfg.get_base_dir(local_or_remote),
            local_or_remote,
            search_str="*",
        )

        to_include_dirnames = [ele for ele in top_level_dirs if ele[:4] != "sub-"]
        to_include_filenames = top_level_files

    elif sub and not ses:  # i.e. "all_non_ses":

        sub_level_dirs, sub_level_files = directories.search_sub_or_ses_level(
            cfg,
            cfg.get_base_dir(local_or_remote),
            local_or_remote,
            sub=sub,
            search_str="*",
        )

        to_include_dirnames = ["/".join([sub, ele]) for ele in sub_level_dirs if (ele[:4] != "ses-" and ele != "histology")]  # TODO: hadle sub level dtype, use cfg sub prefix!!!!!!
        to_include_filenames = ["/".join([sub, ele]) for ele in sub_level_files]

    elif sub and ses:  # i.e. "all_ses_level_non_data_type":

        ses_level_dirs, ses_level_filenames = directories.search_sub_or_ses_level(cfg, cfg.get_base_dir(local_or_remote), local_or_remote, sub=sub, ses=ses, search_str=f"*")

        to_include_dirnames = ["/".join([sub, ses, ele]) for ele in ses_level_dirs if ele not in ["histology", "behav", "ephys", "funcimg"]]
        to_include_filenames = ["/".join([sub, ses, ele]) for ele in ses_level_filenames]

    extra_dirnames += to_include_dirnames
    extra_filenames += to_include_filenames

# -----------------------------------------------------------------------------
# Format Arguments
# -----------------------------------------------------------------------------

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

    see update_list_with_dtype_paths()
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

##
def format_include_lists_into_rclone_args(sub_ses_dtype_include,
                                          extra_dirnames,
                                          extra_filenames):
    """"""
    if any(sub_ses_dtype_incluse_list):
        sub_ses_includes = ["".join([f""" --include "{ele}/**" """ for ele in sub_ses_dtype_incluse_list])]
    else:
        sub_ses_includes = []

    if any(extra_dirnames) or any(extra_filenames):
        extras_includes = ["".join([f""" --include "{ele}/**" """ for ele in extra_dirnames]) + "".join([f""" --include "{ele}" """ for ele in extra_filenames])]
    else:
        extras_includes = []

    include_list = extras_includes + sub_ses_includes
