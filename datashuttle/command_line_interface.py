import argparse
import warnings
from typing import Any, Callable, Dict

import simplejson

from datashuttle import DataShuttle
from datashuttle.configs import canonical_configs, load_configs
from datashuttle.utils import utils

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------


def process_docstring(message: str) -> str:
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
    particular function called (e.g. update_config_file) which calls this
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


def remove_nonetype_entries(dict_: Dict) -> Dict:
    """ """
    return {k: v for k, v in dict_.items() if v is not None}


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
    "-----------------------------------------------------------------------\n"
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
    "-------------------------------------------------------------------------"
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
    filtered_kwargs = remove_nonetype_entries(kwargs)

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


def update_config_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)
    filtered_kwargs = remove_nonetype_entries(kwargs)

    filtered_kwargs = load_configs.handle_cli_or_supplied_config_bools(
        filtered_kwargs
    )

    run_command(project, project.update_config_file, **filtered_kwargs)


# -----------------------------------------------------------------------------
# Setup SSH
# -----------------------------------------------------------------------------


def setup_ssh_connection_to_central_server(*args: Any) -> None:
    """"""
    project = args[0]
    project.setup_ssh_connection_to_central_server()


# -----------------------------------------------------------------------------
# Make Sub Folders
# -----------------------------------------------------------------------------


def make_folders(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = remove_nonetype_entries(kwargs)

    run_command(project, project.make_folders, **filtered_kwargs)


# -----------------------------------------------------------------------------
# Transfer
# -----------------------------------------------------------------------------

# Upload Data -----------------------------------------------------------------


def upload(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = remove_nonetype_entries(kwargs)

    run_command(
        project,
        project.upload,
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


def download(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = remove_nonetype_entries(kwargs)

    run_command(
        project,
        project.download,
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


def upload_specific_folder_or_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.upload_specific_folder_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


# Download Project Folder or File ---------------------------------------------


def download_specific_folder_or_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.download_specific_folder_or_file,
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

# Get Local Path --------------------------------------------------------------


def get_local_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_local_path())


# Get Central Path ------------------------------------------------------------


def get_central_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_central_path())


# Get DataShuttle Path --------------------------------------------------------


def get_datashuttle_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_datashuttle_path())


# Get Config Path -------------------------------------------------------------


def get_config_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_config_path())


# Get Config Path -------------------------------------------------------------


def get_logging_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_logging_path())


# Get Existing Projects -------------------------------------------------------


def get_existing_projects(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_existing_projects())


# Get Next Sub Number --------------------------------------------------------


def get_next_sub_number(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_next_sub_number())


# Get Next Sub Number --------------------------------------------------------


def get_next_ses_number(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)
    print(project.get_next_ses_number(kwargs["sub"]))


# Show Configs ----------------------------------------------------------------


def show_configs(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_configs()


# Show Local Tree -------------------------------------------------------------


def show_local_tree(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_local_tree()


# Show Top Level Folder -------------------------------------------------------


def get_top_level_folder(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_top_level_folder())


# Validate Project  -----------------------------------------------------------


def validate_project(*args: Any) -> None:
    """"""
    project = args[0]
    project.validate_project(error_or_warn="warn", local_only=False)


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
        "central_path", type=str, help=help("required_str")
    )

    make_config_file_parser.add_argument(
        "connection_method", type=str, help=help("required_str")
    )

    make_config_file_parser = make_config_file_parser.add_argument_group(
        "named arguments:"
    )  # type: ignore

    make_config_file_parser.add_argument(
        "--central-host-id",
        "--central_host_id",
        required=False,
        type=str,
        help="(str)",
    )
    make_config_file_parser.add_argument(
        "--central-host-username",
        "--central_host_username",
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

    # Update Config File
    # -------------------------------------------------------------------------

    update_config_file_parser = subparsers.add_parser(
        "update-config-file",
        aliases=["update_config_file"],
        description=f"{process_docstring(DataShuttle.update_config_file.__doc__)}",
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    update_config_file_parser.set_defaults(func=update_config_file)

    config_options = canonical_configs.get_canonical_configs()

    for option in config_options:
        update_config_file_parser.add_argument(
            f"--{option.replace('_', '-')}", f"--{option}", required=False
        )

    # SSH connection to central server
    # ----------------------------------------------------------------------

    setup_ssh_connection_to_central_server_parser = subparsers.add_parser(
        "setup-ssh-connection-to-central-server",
        aliases=["setup_ssh_connection_to_central_server"],
        description=process_docstring(
            DataShuttle.setup_ssh_connection_to_central_server.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    setup_ssh_connection_to_central_server_parser.set_defaults(
        func=setup_ssh_connection_to_central_server
    )

    # Make Sub Folder
    # -------------------------------------------------------------------------

    make_folders_parser = subparsers.add_parser(
        "make-folders",
        aliases=["make_folders"],
        description=process_docstring(DataShuttle.make_folders.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    make_folders_parser = make_folders_parser.add_argument_group(
        "named arguments:"
    )  # type: ignore
    make_folders_parser.set_defaults(func=make_folders)

    make_folders_parser.add_argument(
        "--sub-names",
        "--sub_names",
        "-sub",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    make_folders_parser.add_argument(
        "--ses-names",
        "--ses_names",
        "-ses",
        nargs="+",
        type=str,
        required=False,
        help="Optional: (str, single or multiple) "
        "(selection of datatypes, or 'all')",
    )
    make_folders_parser.add_argument(
        "--datatype",
        "-dt",
        type=str,
        nargs="+",
        required=False,
        default="",  # TODO: this is not nice, should read the default
        # from API NOT duplicate in CLI
        help=help("required_str_single_or_multiple_or_all"),
    )

    # Upload Data
    # -------------------------------------------------------------------------

    upload_parser = subparsers.add_parser(
        "upload",
        description=process_docstring(DataShuttle.upload.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    upload_parser = upload_parser.add_argument_group(
        "named arguments:"
    )  # type: ignore
    upload_parser.set_defaults(func=upload)

    upload_parser.add_argument(
        "--sub-names",
        "--sub_names",
        "-sub",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    upload_parser.add_argument(
        "--ses-names",
        "--ses_names",
        "-ses",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    upload_parser.add_argument(
        "--datatype",
        "-dt",
        type=str,
        nargs="+",
        required=False,
        help="Optional: (str, single or multiple) "
        "(selection of datatypes, or 'all') (default 'all')",
    )
    upload_parser.add_argument(
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

    download_parser = subparsers.add_parser(
        "download",
        description=process_docstring(DataShuttle.download.__doc__),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    download_parser = download_parser.add_argument_group(
        "named arguments:"  # type: ignore
    )
    download_parser.set_defaults(func=download)

    download_parser.add_argument(
        "--sub-names",
        "--sub_names",
        "-sub",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    download_parser.add_argument(
        "--ses-names",
        "--ses_names",
        "-ses",
        type=str,
        nargs="+",
        required=True,
        help=help("required_str_single_or_multiple_or_all"),
    )
    download_parser.add_argument(
        "--datatype",
        "-dt",
        type=str,
        nargs="+",
        required=False,
        help="Optional: (str or list) (selection of data "
        "types, or 'all') (default 'all')",
    )
    download_parser.add_argument(
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

    upload_specific_folder_or_file_parser = subparsers.add_parser(
        "upload-specific-folder-or-file",
        aliases=["upload_specific_folder_or_file"],
        description=process_docstring(
            DataShuttle.upload_specific_folder_or_file.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    upload_specific_folder_or_file_parser.set_defaults(
        func=upload_specific_folder_or_file
    )

    upload_specific_folder_or_file_parser.add_argument(
        "filepath", type=str, help=help("required_str")
    )
    upload_specific_folder_or_file_parser.add_argument(
        "--dry-run",
        "--dry_run",
        action="store_true",
        help=help("flag_default_false"),
    )

    # Download project folder or file
    # -------------------------------------------------------------------------

    download_specific_folder_or_file_parser = subparsers.add_parser(
        "download-specific-folder-or-file",
        aliases=["download_specific_folder_or_file"],
        description=process_docstring(
            DataShuttle.download_specific_folder_or_file.__doc__
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        help="",
    )
    download_specific_folder_or_file_parser.set_defaults(
        func=download_specific_folder_or_file
    )

    download_specific_folder_or_file_parser.add_argument(
        "filepath", type=str, help=help("required_str")
    )
    download_specific_folder_or_file_parser.add_argument(
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

    # Get Local Path
    # -------------------------------------------------------------------------

    get_local_path_parser = subparsers.add_parser(
        "get-local-path",
        aliases=["get_local_path"],
        description=process_docstring(DataShuttle.get_local_path.__doc__),
        help="",
    )
    get_local_path_parser.set_defaults(func=get_local_path)

    # Get Central Path
    # -------------------------------------------------------------------------

    get_central_path_parser = subparsers.add_parser(
        "get-central-path",
        aliases=["get_central_path"],
        description=process_docstring(DataShuttle.get_central_path.__doc__),
        help="",
    )
    get_central_path_parser.set_defaults(func=get_central_path)

    # Get DataShuttle Path
    # -------------------------------------------------------------------------

    get_datashuttle_path_parser = subparsers.add_parser(
        "get-datashuttle-path",
        aliases=["get_datashuttle_path"],
        description=process_docstring(
            DataShuttle.get_datashuttle_path.__doc__
        ),
        help="",
    )
    get_datashuttle_path_parser.set_defaults(func=get_datashuttle_path)

    # Get Config Path
    # -------------------------------------------------------------------------

    get_config_path_parser = subparsers.add_parser(
        "get-config-path",
        aliases=["get_config_path"],
        description=process_docstring(DataShuttle.get_config_path.__doc__),
        help="",
    )
    get_config_path_parser.set_defaults(func=get_config_path)

    # Get Logging Path
    # -------------------------------------------------------------------------

    get_logging_path_parser = subparsers.add_parser(
        "get-logging-path",
        aliases=["get_logging_path"],
        description=process_docstring(DataShuttle.get_logging_path.__doc__),
        help="",
    )
    get_logging_path_parser.set_defaults(func=get_logging_path)

    # Get Existing Projects
    # -------------------------------------------------------------------------

    get_existing_projects_parser = subparsers.add_parser(
        "get-existing-projects",
        aliases=["get_existing_projects"],
        description=process_docstring(
            DataShuttle.get_existing_projects.__doc__
        ),
        help="",
    )
    get_existing_projects_parser.set_defaults(func=get_existing_projects)

    # Get Next Sub Number
    # -------------------------------------------------------------------------

    get_next_sub_number_parser = subparsers.add_parser(
        "get-next-sub-number",
        aliases=["get_next_sub_number"],
        description="Get the next subject number across "
        "local and central machines.",
        help="",
    )
    get_next_sub_number_parser.set_defaults(func=get_next_sub_number)

    # Get Next Ses Number
    # -------------------------------------------------------------------------

    get_next_ses_number_parser = subparsers.add_parser(
        "get-next-ses-number",
        aliases=["get_next_ses_number"],
        description="Get the next session number across "
        "local and central machines.",
        help="",
    )
    get_next_ses_number_parser.set_defaults(func=get_next_ses_number)

    get_next_ses_number_parser.add_argument(
        "sub",
        type=str,
        help="Required: (str) sub to find latest session for.",
    )

    # Show Configs
    # -------------------------------------------------------------------------

    show_configs_parser = subparsers.add_parser(
        "show-configs",
        aliases=["show_configs"],
        description=process_docstring(DataShuttle.show_configs.__doc__),
        help="",
    )
    show_configs_parser.set_defaults(func=show_configs)

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

    get_top_level_folder_parser = subparsers.add_parser(
        "get-top-level-folder",
        aliases=["get_top_level_folder"],
        description=process_docstring(
            DataShuttle.get_top_level_folder.__doc__
        ),
        help="",
    )
    get_top_level_folder_parser.set_defaults(func=get_top_level_folder)

    # Validate Project
    # -------------------------------------------------------------------------

    validate_project_parser = subparsers.add_parser(
        "validate-project",
        aliases=["validate_project"],
        description=process_docstring(DataShuttle.validate_project.__doc__),
        help="",
    )
    validate_project_parser.set_defaults(func=validate_project)

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
    Suppress the warning that a config file must
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
    project = DataShuttle(args.project_name, print_startup_message=False)
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
