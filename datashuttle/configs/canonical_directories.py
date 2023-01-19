from datashuttle.utils.directory_class import Directory

from .configs import Configs


def get_reserved_filetransfer_keywords(level: str) -> list:
    """ """
    if level == "sub":
        keywords = ["all_sub", "all_non_sub"]

    elif level == "ses":
        keywords = ["all_ses", "all_non_ses"]

    elif level == "data_type":
        keywords = ["all_data_type", "all_ses_level_non_data_type"]

    return keywords


def get_data_type_directories(cfg: Configs) -> dict:
    """
    This function holds the canonical directories
    managed by datashuttle.

    Parameters
    ----------

    cfg : datashuttle configs dict

    Other Parameters
    ----------------

    When adding a new directory, the
    key should be the canonical key used to refer
    to the data_type in datashuttle and SWC-BIDs.

    The value is a Directory() class instance with
    the required fields

    name : The display name for the data_type, that will
        be used for making and transferring files in practice.
        This should always match the canonical name, but left as
        an option for rare cases in which advanced users want to change it.

    used : whether the dirctory is used or not (see make_config_file)
        if False, the directory will not be made in make_sub_dir
        even if selected.

    level : "sub" or "ses", level to make the directory at.

    Notes
    ------

    In theory, adding a new  directory should only require
    adding an entry to this dictionary. However, this will not
    update configs e.g. use_xxx. This has not been
    directly tested yet, but if it does not work when attempted
    it should be configured to from then on.
    """
    return {
        "ephys": Directory(
            name="ephys",
            used=cfg["use_ephys"],
            level="ses",
        ),
        "behav": Directory(
            name="behav",
            used=cfg["use_behav"],
            level="ses",
        ),
        "funcimg": Directory(
            name="funcimg",
            used=cfg["use_funcimg"],
            level="ses",
        ),
        "histology": Directory(
            name="histology",
            used=cfg["use_histology"],
            level="sub",
        ),
    }


def get_data_type_directories_by_level(
    level: str, used_only: bool, as_str: bool, cfg: Configs
):  # TODO: DOC!

    directories = [
        dir
        for dir in get_data_type_directories(cfg).values()
        if dir.level == level
    ]

    if used_only:
        directories = [dir for dir in directories if dir.used]

    if as_str:
        directories = [dir.name for dir in directories]

    return directories
