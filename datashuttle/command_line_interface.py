import argparse
import warnings
from typing import Any, Callable

import simplejson

from datashuttle.configs import load_configs
from datashuttle.datashuttle import DataShuttle
from datashuttle.utils import utils

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------


def process_docstring(message):
    """
    Sphinx is quite specific about the docstrings allowed
    """
    message = message.replace("-", "")
    message = message.split("Parameters")[0]
    return message


def run_command(
    project: DataShuttle, function: Callable, *args: Any, **kwargs: Any
) -> None:
    """
    Central function for running any methods command. The CLI
    interface works as a wrapper around datashuttle methods.
    On CLI call, a project with passed project_name is initialised.
    This is then passed to the CLI wrapper of the
    particular function called (e.g. update_config) which calls this
    function with the appropriate methods and arguments to call
    datashuttle.

    Note the arguments from the CLI are passed directly to the
    datashuttle function and so CLI arguments MUST match exactly
    the argument names on the datashuttle API. argparse will convert
    dash to underscore for stored variable names.

    If project is projected (see PROTECTED_TEST_PROJECT_NAME),
    dump the variables to stdout, so they can be checked.
    Otherwise, run the DataShuttle function.

    Parameters
    ----------

    project : an initialised DataShuttle project
        e.g. project = DataShuttle("project_name")

    function : datashuttle function to call, e.g.
        project.make_config_file. Note this is the
        actual function object.

    *args : positional args to call the function with

    **kwargs : keyword arguments to call the function with.
    """
    if project.project_name == PROTECTED_TEST_PROJECT_NAME:
        print("TEST_OUT_START: ", simplejson.dumps([args, kwargs]))
    else:
        function(*args, **kwargs)


def make_kwargs(args: Any) -> dict:
    """
    Turn the list of arguments passed to the CLI
    to keyword arguments. Remove the project name
    and "func" args which are also included by default.
    """
    kwargs = vars(args)
    del kwargs["func"]
    del kwargs["project_name"]
    return kwargs


def help(help_type: str) -> str:
    """
    Convenience function to hold frequently used
    argument help strings.
    """
    if help_type == "flag_default_false":
        help_str = "flag (default False)"

    elif help_type == "required_str":
        help_str = "Required: (str)"

    elif help_type == "optional_flag_default_false":
        help_str = "Optional: flag (default False)"

    elif help_type == "required_str_single_or_multiple":
        help_str = "Required: (str, single or multiple)"

    elif help_type == "required_str_single_or_multiple_or_all":
        help_str = "Required: (str, single or multiple) ('all' for all)"

    return help_str


# -----------------------------------------------------------------------------
# Entry Point to the CLI
# -----------------------------------------------------------------------------

description = (
    "----------------------------------------------------------------------\n"
    "DataShuttle command line interface. "
    "\n\n"
    "datashuttle [PROJECT NAME] [COMMAND] [OPTIONS]"
    "\n\n"
    "To get detailed help for commands and their optional arguments, "
    "\ntype datashuttle [PROJECT NAME] [COMMAND] --help'"
    "\n\n"
    "On first use it is necessary to setup configurations. \ne.g."
    "'datashuttle [PROJECT NAME] make-config-file [OPTIONS]'"
    "\n\n"
    "see \n'datashuttle <project_name> make-config-file --help'"
    "\nfor full list of options."
    "\n\n"
    "All command and argument names are matched to the API "
    "documentation. "
    "\n\n"
    "----------------------------------------------------------------------"
)

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------


def make_config_file(project: DataShuttle, args: Any) -> None:
    """
    Run make_config_file on datashuttle API after processing CLI
    arguments. handle_cli_or_supplied_config_bools() will turn
    string representation of bool and None into python datatypes.
    """
    kwargs = make_kwargs(args)
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    filtered_kwargs = load_configs.handle_cli_or_supplied_config_bools(
        filtered_kwargs
    )

    run_command(
        project,
        project.make_config_file,
        **filtered_kwargs,
    )


# -----------------------------------------------------------------------------
# Update Config
# -----------------------------------------------------------------------------


def update_config(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)
    option_key = kwargs["option_key"]
    option_key = option_key.replace("-", "_")
    new_info = kwargs["new_info"]

    run_command(
        project,
        project.update_config,
        option_key,
        new_info,
    )


# -----------------------------------------------------------------------------
# Setup SSH
# -----------------------------------------------------------------------------


def setup_ssh_connection_to_remote_server(*args: Any) -> None:
    """"""
    project = args[0]
    project.setup_ssh_connection_to_remote_server()


# -----------------------------------------------------------------------------
# Make Sub Folders
# -----------------------------------------------------------------------------


def make_sub_folders(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(project, project.make_sub_folders, **filtered_kwargs)


# -----------------------------------------------------------------------------
# Transfer
# -----------------------------------------------------------------------------

# Upload Data -----------------------------------------------------------------


def upload_data(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(
        project,
        project.upload_data,
        **filtered_kwargs,
    )


# Upload All ------------------------------------------------------------------


def upload_all(*args: Any) -> None:
    """"""
    project = args[0]
    project.upload_all()


# Upload Entire Project -------------------------------------------------------


def upload_entire_project(*args: Any) -> None:
    """"""
    project = args[0]
    project.upload_entire_project()


# Download Data ---------------------------------------------------------------


def download_data(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(
        project,
        project.download_data,
        **filtered_kwargs,
    )


# Download All ----------------------------------------------------------------


def download_all(*args: Any) -> None:
    """"""
    project = args[0]
    project.download_all()


# Download Entire Project -----------------------------------------------------


def download_entire_project(*args: Any) -> None:
    """"""
    project = args[0]
    project.download_entire_project()


# Upload Project Folder or File -----------------------------------------------


def upload_project_folder_or_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.upload_project_folder_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


# Download Project Folder or File ---------------------------------------------


def download_project_folder_or_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.download_project_folder_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


# Set Top Level Folder or File ------------------------------------------------


def set_top_level_folder(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.set_top_level_folder,
        kwargs["folder_name"],
    )


# -----------------------------------------------------------------------------
# Getters
# -----------------------------------------------------------------------------
# Almost worth creating a function factory for these, only thing that changes is
# DataShuttle function. But code would be hard to understand and only 4 cases...

# Get Local Path --------------------------------------------------------------


def show_local_path(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_local_path()


# Get Appdir Path -------------------------------------------------------------


def show_datashuttle_path(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_datashuttle_path()


# Get Config Path -------------------------------------------------------------


def show_config_path(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_config_path()


# Get Remote Path -------------------------------------------------------------


def show_remote_path(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_remote_path()


# Show Configs ----------------------------------------------------------------


def show_configs(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_configs()


# Show Logging Path ----------------------------------------------------------


def show_logging_path(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_logging_path()


# Show Local Tree -------------------------------------------------------------


def show_local_tree(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_local_tree()


# Show Top Level Folder -------------------------------------------------------


def show_top_level_folder(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_top_level_folder()


# Show Next Sub Number -------------------------------------------------------


def show_next_sub_number(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_next_sub_number()


# Show Next Sub Number -------------------------------------------------------


def show_next_ses_number(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)
    project.show_next_ses_number(kwargs["sub"])


# Check Name Processing -------------------------------------------------------


def check_name_formatting(project: DataShuttle, args: Any) -> None:

    kwargs = make_kwargs(args)

    run_command(
        project,
        project.check_name_formatting,
        kwargs.pop("names"),
        **kwargs,
    )


# Supply Own Config -----------------------------------------------------------


def supply_config_file(project: DataShuttle, args: Any) -> None:

    kwargs = make_kwargs(args)

    run_command(
        project,
        project.supply_config_file,
        kwargs["path_to_config"],
    )


def construct_parser():
    """
    Return the argparse argument parser. This
    is required to be a function for docs building
    with sphinx-argparse.
    """
    parser = argparse.ArgumentParser(
        prog="datashuttle",
        usage="%(prog)s [PROJECT NAME]",  # old-style format required
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        dest="project_name",
    )
    subparsers = parser.add_subparsers()

    # Make Config File
    # -------------------------------------------------------------------------

    make_config_file_parser = subparsers.add_parser(
        "make-config-file",
        aliases=["make_config_file"],
        description=process_docstring(DataShuttle.make_config_file.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    make_config_file_parser.set_defaults(func=make_config_file)

    make_config_file_parser.add_argument(
        "local_path", type=str, help=help("required_str")
    )

    make_config_file_parser.add_argument(
        "remote_path", type=str, help=help("required_str")
    )

    make_config_file_parser.add_argument(
        "connection_method", type=str, help=help("required_str")
    )

    make_config_file_parser = make_config_file_parser.add_argument_group(
        "named arguments:"
    )  # type: ignore

    make_config_file_parser.add_argument(
        "--remote-host-id",
        "--remote_host_id",
        required=False,
        type=str,
        help="(str)",
    )
    make_config_file_parser.add_argument(
        "--remote-host-username",
        "--remote_host_username",
        required=False,
        help="(str)",
    )
    make_config_file_parser.add_argument(
        "--overwrite-old-files",
        "--overwrite_old_files",
        required=False,
        action="store_true",
        help=help("flag_default_false"),
    )
    make_config_file_parser.add_argument(
        "--transfer-verbosity",
        "--transfer_verbosity",
        required=False,
        help="(str)",
    )
    make_config_file_parser.add_argument(
        "--show-transfer-progress",
        "--show_transfer_progress",
        required=False,
        action="store_true",
        help=help("flag_default_false"),
    )
    make_config_file_parser.add_argument(
        "--use-ephys",
        "--use_ephys",
        required=False,
        action="store_true",
        help=help("flag_default_false"),
    )
    make_config_file_parser.add_argument(
        "--use-behav",
        "--use_behav",
        required=False,
        action="store_true",
        help=help("flag_default_false"),
    )
    make_config_file_parser.add_argument(
        "--use-funcimg",
        "--use_funcimg",
        required=False,
        action="store_true",
        help=help("flag_default_false"),
    )
    make_config_file_parser.add_argument(
        "--use-histology",
        "--use_histology",
        required=False,
        action="store_true",
        help=help("flag_default_false"),
    )

    make_config_file_parser = subparsers.add_parser(
        "update-config",
        aliases=["update_config"],
        description=f"{process_docstring(DataShuttle.update_config.__doc__)} "
        f"\nThe option key should be in the form of config file keys"
        f"(e.g. remote_path, local_path)\n"
        f"EXAMPLE: datashuttle test update_config remote_path 'test_path'",
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    make_config_file_parser.set_defaults(func=update_config)

    make_config_file_parser.add_argument(
        "option_key",
        action="store",
        help="(str) (see make_config_file --help)",
    )
    make_config_file_parser.add_argument(
        "new_info",
        action="store",
        help="(str or bool) depending on option key",
    )

    # SSH connection to remote server
    # ----------------------------------------------------------------------

    setup_ssh_connection_to_remote_server_parser = subparsers.add_parser(
        "setup-ssh-connection-to-remote-server",
        aliases=["setup_ssh_connection_to_remote_server"],
        description=process_docstring(
            DataShuttle.setup_ssh_connection_to_remote_server.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    setup_ssh_connection_to_remote_server_parser.set_defaults(
        func=setup_ssh_connection_to_remote_server
    )

    # Make Sub Folder
    # ----------------------------------------------------------------------

    make_sub_folders_parser = subparsers.add_parser(
        "make-sub-folders",
        aliases=["make_sub_folders"],
        description=process_docstring(DataShuttle.make_sub_folders.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    make_sub_folders_parser = make_sub_folders_parser.add_argument_group(
        "named arguments:"
    )  # type: ignore
    make_sub_folders_parser.set_defaults(func=make_sub_folders)

    make_sub_folders_parser.add_argument(
        "--sub-names",
        "--sub_names",
        "-sub",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    make_sub_folders_parser.add_argument(
        "--ses-names",
        "--ses_names",
        "-ses",
        nargs="+",
        type=str,
        required=False,
        help="Optional: (str, single or multiple) (selection of data types, or 'all')",
    )
    make_sub_folders_parser.add_argument(
        "--data-type",
        "--data_type",
        "-dt",
        type=str,
        nargs="+",
        required=False,
        default="all",  # TODO: this is not nice, should read the default from API NOT duplicate in CLI
        help=help("required_str_single_or_multiple_or_all"),
    )

    # Upload Data
    # ----------------------------------------------------------------------

    upload_data_parser = subparsers.add_parser(
        "upload-data",
        aliases=["upload_data"],
        description=process_docstring(DataShuttle.upload_data.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    upload_data_parser = upload_data_parser.add_argument_group(
        "named arguments:"
    )  # type: ignore
    upload_data_parser.set_defaults(func=upload_data)

    upload_data_parser.add_argument(
        "--sub-names",
        "--sub_names",
        "-sub",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    upload_data_parser.add_argument(
        "--ses-names",
        "--ses_names",
        "-ses",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    upload_data_parser.add_argument(
        "--data-type",
        "--data_type",
        "-dt",
        type=str,
        nargs="+",
        required=False,
        help="Optional: (str, single or multiple) (selection of data types, or 'all') (default 'all')",
    )
    upload_data_parser.add_argument(
        "--dry-run",
        "--dry_run",
        required=False,
        action="store_true",
        help=help("optional_flag_default_false"),
    )

    # Upload All
    # -------------------------------------------------------------------------

    upload_all_parser = subparsers.add_parser(
        "upload-all",
        aliases=["upload_all"],
        description=process_docstring(DataShuttle.upload_all.__doc__),
        help="",
    )
    upload_all_parser.set_defaults(func=upload_all)

    # Upload All
    # -------------------------------------------------------------------------

    upload_entire_project_parser = subparsers.add_parser(
        "upload-entire-project",
        aliases=["upload_entire_project"],
        description=process_docstring(
            DataShuttle.upload_entire_project.__doc__
        ),
        help="",
    )
    upload_entire_project_parser.set_defaults(func=upload_entire_project)

    # Download Data
    # -------------------------------------------------------------------------

    download_data_parser = subparsers.add_parser(
        "download-data",
        aliases=["download_data"],
        description=process_docstring(DataShuttle.download_data.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    download_data_parser = download_data_parser.add_argument_group(
        "named arguments:"  # type: ignore
    )
    download_data_parser.set_defaults(func=download_data)

    download_data_parser.add_argument(
        "--sub-names",
        "--sub_names",
        "-sub",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    download_data_parser.add_argument(
        "--ses-names",
        "--ses_names",
        "-ses",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    download_data_parser.add_argument(
        "--data-type",
        "--data_type",
        "-dt",
        type=str,
        nargs="+",
        required=False,
        help="Optional: (str or list) (selection of data "
        "types, or 'all') (default 'all')",
    )
    download_data_parser.add_argument(
        "--dry-run",
        "--dry_run",
        required=False,
        action="store_true",
        help=help("optional_flag_default_false"),
    )

    # Download All
    # -------------------------------------------------------------------------

    download_all_parser = subparsers.add_parser(
        "download-all",
        aliases=["download_all"],
        description=process_docstring(DataShuttle.download_all.__doc__),
        help="",
    )
    download_all_parser.set_defaults(func=download_all)

    # Download Entire Project
    # -------------------------------------------------------------------------

    download_entire_project_parser = subparsers.add_parser(
        "download-entire-project",
        aliases=["download_entire_project"],
        description=process_docstring(
            DataShuttle.download_entire_project.__doc__
        ),
        help="",
    )
    download_entire_project_parser.set_defaults(func=download_entire_project)

    # Upload project folder or file
    # -------------------------------------------------------------------------

    upload_project_folder_or_file_parser = subparsers.add_parser(
        "upload-project-folder-or-file",
        aliases=["upload_project_folder_or_file"],
        description=process_docstring(
            DataShuttle.upload_project_folder_or_file.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    upload_project_folder_or_file_parser.set_defaults(
        func=upload_project_folder_or_file
    )

    upload_project_folder_or_file_parser.add_argument(
        "filepath", type=str, help=help("required_str")
    )
    upload_project_folder_or_file_parser.add_argument(
        "--dry-run",
        "--dry_run",
        action="store_true",
        help=help("flag_default_false"),
    )

    # Download project folder or file
    # -------------------------------------------------------------------------

    download_project_folder_or_file_parser = subparsers.add_parser(
        "download-project-folder-or-file",
        aliases=["download_project_folder_or_file"],
        description=process_docstring(
            DataShuttle.download_project_folder_or_file.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    download_project_folder_or_file_parser.set_defaults(
        func=download_project_folder_or_file
    )

    download_project_folder_or_file_parser.add_argument(
        "filepath", type=str, help=help("required_str")
    )
    download_project_folder_or_file_parser.add_argument(
        "--dry-run",
        "--dry_run",
        action="store_true",
        help=help("flag_default_false"),
    )

    # Set Top Level Folder
    # -------------------------------------------------------------------------

    set_top_level_folder_parser = subparsers.add_parser(
        "set-top-level-folder",
        aliases=["set_top_level_folder"],
        description=process_docstring(
            DataShuttle.set_top_level_folder.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    set_top_level_folder_parser.set_defaults(func=set_top_level_folder)

    set_top_level_folder_parser.add_argument(
        "folder_name",
        type=str,
        help=help("required_str"),
    )

    # Show Local Path
    # -------------------------------------------------------------------------

    show_local_path_parser = subparsers.add_parser(
        "show-local-path",
        aliases=["show_local_path"],
        description=process_docstring(DataShuttle.show_local_path.__doc__),
        help="",
    )
    show_local_path_parser.set_defaults(func=show_local_path)

    show_datashuttle_path_parser = subparsers.add_parser(
        "show-datashuttle-path",
        aliases=["show_datashuttle_path"],
        description=process_docstring(
            DataShuttle.show_datashuttle_path.__doc__
        ),
        help="",
    )
    show_datashuttle_path_parser.set_defaults(func=show_datashuttle_path)

    # Get Config Path
    # -------------------------------------------------------------------------

    show_config_path_parser = subparsers.add_parser(
        "show-config-path",
        aliases=["show_config_path"],
        description=process_docstring(DataShuttle.show_config_path.__doc__),
        help="",
    )
    show_config_path_parser.set_defaults(func=show_config_path)

    # Get Remote Path
    # -------------------------------------------------------------------------

    show_remote_path_parser = subparsers.add_parser(
        "show-remote-path",
        aliases=["show_remote_path"],
        description=process_docstring(DataShuttle.show_remote_path.__doc__),
        help="",
    )
    show_remote_path_parser.set_defaults(func=show_remote_path)

    # Show Configs
    # -------------------------------------------------------------------------

    show_configs_parser = subparsers.add_parser(
        "show-configs",
        aliases=["show_configs"],
        description=process_docstring(DataShuttle.show_configs.__doc__),
        help="",
    )
    show_configs_parser.set_defaults(func=show_configs)

    # Show Logging Path
    # -------------------------------------------------------------------------

    show_logging_path_parser = subparsers.add_parser(
        "show-logging-path",
        aliases=["show_logging_path"],
        description=process_docstring(DataShuttle.show_logging_path.__doc__),
        help="",
    )
    show_logging_path_parser.set_defaults(func=show_logging_path)

    # Show Local tree
    # -------------------------------------------------------------------------

    show_local_tree_parser = subparsers.add_parser(
        "show-local-tree",
        aliases=["show_local_tree"],
        description=process_docstring(DataShuttle.show_local_tree.__doc__),
        help="",
    )
    show_local_tree_parser.set_defaults(func=show_local_tree)

    # Show Top Level Folder
    # -------------------------------------------------------------------------

    show_top_level_folder_parser = subparsers.add_parser(
        "show-top-level-folder",
        aliases=["show_top_level_folder"],
        description=process_docstring(
            DataShuttle.show_top_level_folder.__doc__
        ),
        help="",
    )
    show_top_level_folder_parser.set_defaults(func=show_top_level_folder)

    # Show Next Sub Number
    # -------------------------------------------------------------------------

    show_next_sub_number_parser = subparsers.add_parser(
        "show-next-sub-number",
        aliases=["show_next_sub_number"],
        description=process_docstring(
            DataShuttle.show_next_sub_number.__doc__
        ),
        help="",
    )
    show_next_sub_number_parser.set_defaults(func=show_next_sub_number)

    # Show Next Ses Number
    # -------------------------------------------------------------------------

    show_next_ses_number_parser = subparsers.add_parser(
        "show-next-ses-number",
        aliases=["show_next_ses_number"],
        description=process_docstring(
            DataShuttle.show_next_ses_number.__doc__
        ),
        help="",
    )
    show_next_ses_number_parser.set_defaults(func=show_next_ses_number)

    show_next_ses_number_parser.add_argument(
        "sub",
        type=str,
        help="Required: (str) sub to find latest session for.",
    )

    # Check Name Processing
    # -------------------------------------------------------------------------

    check_name_formatting_parser = subparsers.add_parser(
        "check-name-formatting",
        aliases=["check_name_formatting"],
        description=process_docstring(
            DataShuttle.check_name_formatting.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    check_name_formatting_parser.set_defaults(func=check_name_formatting)

    check_name_formatting_parser.add_argument(
        "prefix",
        type=str,
        help="Required: (str) (sub- or ses-)",
    )

    check_name_formatting_parser.add_argument(
        "--names",
        type=str,
        nargs="+",
        help="Required: (str, single or multiple)",
    )

    # Supply Config
    # -------------------------------------------------------------------------

    supply_config_file_parser = subparsers.add_parser(
        "supply-config-file",
        aliases=["supply_config_file"],
        description=process_docstring(DataShuttle.supply_config_file.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    supply_config_file_parser.set_defaults(func=supply_config_file)

    supply_config_file_parser.add_argument(
        "path_to_config",
        type=str,
        help="Required: (str, single or multiple)",
    )

    return parser


parser = construct_parser()

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------


def main() -> None:
    """
    All arguments from the CLI are collected and
    the function to call determined from the func
    properly on the CLI args. This command name
    should match the datashuttle API function name.

    Next, initialise a datashuttle project using the API.
    Supress the warning that a config file must
    be made on project initialisation when
    a config is being made.

    Finally, call the function associated with the command
    This is setup above, using the "set defaults" function
    associated with created parsers, e.g.

    supply_config_file_parser.set_defaults(func=supply_config_file)

    These command functions (all defined above) will process
    the CLI arguments and then call the appropriate API function
    through run_command().
    """
    args = parser.parse_args()

    if "func" in args and str(args.func.__name__) == "make_config_file":
        warn = "ignore"
    else:
        warn = "default"

    warnings.filterwarnings(warn)  # type: ignore
    project = DataShuttle(args.project_name)
    warnings.filterwarnings("default")

    if len(vars(args)) > 1:
        args.func(project, args)
    else:
        utils.print_message_to_user(
            f"Datashuttle project: {args.project_name}. "
            f"Add additional commands, see --help for details"
        )


if __name__ == "__main__":
    main()
