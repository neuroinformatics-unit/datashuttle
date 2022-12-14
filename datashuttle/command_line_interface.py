import argparse
import warnings
from typing import Any, Callable

import simplejson

from datashuttle.datashuttle import DataShuttle
from datashuttle.utils_mod import canonical_configs

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"


# ------------------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------------------


def run_command(
    project: DataShuttle, function: Callable, *args: Any, **kwargs: Any
) -> None:
    """
    If project is protected test name, dump the variables to
    stdout so they can be checked. Otherwise, run the
    DataShuttle function.
    """
    if project.project_name == PROTECTED_TEST_PROJECT_NAME:
        print("TEST_OUT_START: ", simplejson.dumps([args, kwargs]))
    else:
        function(*args, **kwargs)


def make_kwargs(args: Any) -> dict:
    kwargs = vars(args)
    del kwargs["func"]
    del kwargs["project_name"]
    return kwargs


def help(help_type: str) -> str:
    """ """

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


# ------------------------------------------------------------------------------------------
# Entry
# ------------------------------------------------------------------------------------------

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
    "'datashuttle [PROJECT NAME] make_config_file [OPTIONS]'"
    "\n\n"
    "see \n'datashuttle <project_name> make_config_file --help'"
    "\nfor full list of options."
    "\n\n"
    "All command and argument names are matched to the API "
    "documentation. "
    "\n\n"
    "----------------------------------------------------------------------"
)

parser = argparse.ArgumentParser(
    prog="datashuttle",
    usage="%(prog)s [PROJECT NAME]",  # old-style format required
    description=description,
    formatter_class=argparse.RawTextHelpFormatter,
)

project_name_argument = parser.add_argument(
    dest="project_name",
)
subparsers = parser.add_subparsers(metavar="\ncommands:")


# ------------------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------------------


def make_config_file(project: DataShuttle, args: Any) -> None:
    kwargs = make_kwargs(args)
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    filtered_kwargs = canonical_configs.handle_cli_or_supplied_config_bools(
        filtered_kwargs
    )

    run_command(
        project,
        project.make_config_file,
        **filtered_kwargs,
    )


make_config_file_parser = subparsers.add_parser(
    "make-config-file",
    aliases=["make_config_file"],
    description=DataShuttle.make_config_file.__doc__,
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
    metavar="",
    help="(str)",
)
make_config_file_parser.add_argument(
    "--remote-host-username",
    "--remote_host_username",
    required=False,
    help="(str)",
    metavar="",
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


# ------------------------------------------------------------------------------------------
# Update Config
# ------------------------------------------------------------------------------------------


def update_config(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)
    option_key = kwargs["option_key"]
    new_info = kwargs["new_info"]

    new_info = canonical_configs.handle_bool(option_key, new_info)

    run_command(
        project,
        project.update_config,
        option_key,
        new_info,
    )


make_config_file_parser = subparsers.add_parser(
    "update-config",
    aliases=["update_config"],
    description=f"{DataShuttle.update_config.__doc__} "
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
    "new_info", action="store", help="(str or bool) depending on option key"
)


# ------------------------------------------------------------------------------------------
# Setup SSH
# ------------------------------------------------------------------------------------------


def setup_ssh_connection_to_remote_server(*args: Any) -> None:
    """"""
    project = args[0]
    project.setup_ssh_connection_to_remote_server()


setup_ssh_connection_to_remote_server_parser = subparsers.add_parser(
    "setup-ssh-connection-to-remote-server",
    aliases=["setup_ssh_connection_to_remote_server"],
    description=DataShuttle.setup_ssh_connection_to_remote_server.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
setup_ssh_connection_to_remote_server_parser.set_defaults(
    func=setup_ssh_connection_to_remote_server
)


# ------------------------------------------------------------------------------------------
# Make Sub Dirs
# ------------------------------------------------------------------------------------------


def make_sub_dir(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(project, project.make_sub_dir, **filtered_kwargs)


make_sub_dir_parser = subparsers.add_parser(
    "make-sub-dir",
    aliases=["make_sub_dir"],
    description=DataShuttle.make_sub_dir.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
make_sub_dir_parser = make_sub_dir_parser.add_argument_group(
    "named arguments:"
)  # type: ignore
make_sub_dir_parser.set_defaults(func=make_sub_dir)


make_sub_dir_parser.add_argument(
    "--sub-names",
    "--sub_names",
    type=str,
    nargs="+",
    required=True,
    help=help("required_str_single_or_multiple_or_all"),
    metavar="",
)
make_sub_dir_parser.add_argument(
    "--ses-names",
    "--ses_names",
    nargs="+",
    type=str,
    required=False,
    help="Optional: (str, single or multiple) (selection of data types, or 'all')",
    metavar="",
)
make_sub_dir_parser.add_argument(
    "--experiment-type",
    "--experiment_type",
    type=str,
    nargs="+",
    required=True,
    help=help("required_str_single_or_multiple_or_all"),
    metavar="",
)


# ------------------------------------------------------------------------------------------
# Transfer
# ------------------------------------------------------------------------------------------

# Upload Data --------------------------------------------------------------------------


def upload_data(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.upload_data,
        **kwargs,
    )


upload_data_parser = subparsers.add_parser(
    "upload-data",
    aliases=["upload_data"],
    description=DataShuttle.upload_data.__doc__,
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
    type=str,
    nargs="+",
    required=True,
    help=help("required_str_single_or_multiple_or_all"),
    metavar="",
)
upload_data_parser.add_argument(
    "--ses-names",
    "--ses_names",
    type=str,
    nargs="+",
    required=True,
    help=help("required_str_single_or_multiple_or_all"),
    metavar="",
)
upload_data_parser.add_argument(
    "--experiment-type",
    "--experiment_type",
    type=str,
    nargs="+",
    required=False,
    help="Optional: (str, single or multiple) (selection of data types, or 'all') (default 'all')",
    metavar="",
)
upload_data_parser.add_argument(
    "--dry-run",
    "--dry_run",
    required=False,
    action="store_true",
    help=help("optional_flag_default_false"),
)


# Download Data --------------------------------------------------------------------------


def download_data(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.download_data,
        **kwargs,
    )


download_data_parser = subparsers.add_parser(
    "download-data",
    aliases=["download_data"],
    description=DataShuttle.download_data.__doc__,
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
    type=str,
    nargs="+",
    required=True,
    help=help("required_str_single_or_multiple_or_all"),
    metavar="",
)
download_data_parser.add_argument(
    "--ses-names",
    "--ses_names",
    type=str,
    nargs="+",
    required=True,
    help=help("required_str_single_or_multiple_or_all"),
    metavar="",
)
download_data_parser.add_argument(
    "--experiment-type",
    "--experiment_type",
    type=str,
    nargs="+",
    required=False,
    help="Optional: (str or list) (selection of data types, or 'all') (default 'all')",
    metavar="",
)
download_data_parser.add_argument(
    "--dry-run",
    "--dry_run",
    required=False,
    action="store_true",
    help=help("optional_flag_default_false"),
)


# Upload Project Dir or File -----------------------------------------------------------


def upload_project_dir_or_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.upload_project_dir_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


upload_project_dir_or_file_parser = subparsers.add_parser(
    "upload-project-dir-or-file",
    aliases=["upload_project_dir_or_file"],
    description=DataShuttle.upload_project_dir_or_file.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
upload_project_dir_or_file_parser.set_defaults(func=upload_project_dir_or_file)

upload_project_dir_or_file_parser.add_argument(
    "filepath", type=str, help=help("required_str")
)
upload_project_dir_or_file_parser.add_argument(
    "--dry-run",
    "--dry_run",
    action="store_true",
    help=help("flag_default_false"),
)


# Download Project Dir or File ---------------------------------------------------------


def download_project_dir_or_file(project: DataShuttle, args: Any) -> None:
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.download_project_dir_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


download_project_dir_or_file_parser = subparsers.add_parser(
    "download-project-dir-or-file",
    aliases=["download_project_dir_or_file"],
    description=DataShuttle.download_project_dir_or_file.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
download_project_dir_or_file_parser.set_defaults(
    func=download_project_dir_or_file
)

download_project_dir_or_file_parser.add_argument(
    "filepath", type=str, help=help("required_str")
)
download_project_dir_or_file_parser.add_argument(
    "--dry-run",
    "--dry_run",
    action="store_true",
    help=help("flag_default_false"),
)


# ------------------------------------------------------------------------------------------
# Getters
# ------------------------------------------------------------------------------------------
# Almost worth creating a function factory for these, only thing that changes is
# DataShuttle function. But code would be hard to understand and only 4 cases...

# Get Local Path --------------------------------------------------------------------------


def get_local_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_local_path())


get_local_path_parser = subparsers.add_parser(
    "get-local-path",
    aliases=["get_local_path"],
    description=DataShuttle.get_local_path.__doc__,
)
get_local_path_parser.set_defaults(func=get_local_path)


# Get Appdir Path --------------------------------------------------------------------------


def get_appdir_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_appdir_path())


get_appdir_path_parser = subparsers.add_parser(
    "get-appdir-path",
    aliases=["get_appdir_path"],
    description=DataShuttle.get_appdir_path.__doc__,
)
get_appdir_path_parser.set_defaults(func=get_appdir_path)


# Get Config Path --------------------------------------------------------------------------


def get_config_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_config_path())


get_config_path_parser = subparsers.add_parser(
    "get-config-path",
    aliases=["get_config_path"],
    description=DataShuttle.get_config_path.__doc__,
)
get_config_path_parser.set_defaults(func=get_config_path)


# Get Remote Path --------------------------------------------------------------------------


def get_remote_path(*args: Any) -> None:
    """"""
    project = args[0]
    print(project.get_remote_path())


get_remote_path_parser = subparsers.add_parser(
    "get-remote-path",
    aliases=["get_remote_path"],
    description=DataShuttle.get_remote_path.__doc__,
)
get_remote_path_parser.set_defaults(func=get_remote_path)


# Show Configs --------------------------------------------------------------------------


def show_configs(*args: Any) -> None:
    """"""
    project = args[0]
    project.show_configs()


show_configs_parser = subparsers.add_parser(
    "show-configs",
    aliases=["show_configs"],
    description=DataShuttle.show_configs.__doc__,
)
show_configs_parser.set_defaults(func=show_configs)

# Check Name Processing --------------------------------------------------------------------------


def check_name_processing(project: DataShuttle, args: Any) -> None:

    kwargs = make_kwargs(args)

    run_command(
        project,
        project.check_name_processing,
        kwargs.pop("names"),
        **kwargs,
    )


check_name_processing_parser = subparsers.add_parser(
    "check-name-processing",
    aliases=["check_name_processing"],
    description=DataShuttle.check_name_processing.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
check_name_processing_parser.set_defaults(func=check_name_processing)

check_name_processing_parser.add_argument(
    "names",
    type=str,
    nargs="+",
    help="Required: (str, single or multiple)",
)

check_name_processing_parser.add_argument(
    "--prefix",
    type=str,
    help="Required: (str)",
)


# Supply Own Config ------------------------------------------------------------------------

#
def supply_config_file(project: DataShuttle, args: Any) -> None:

    kwargs = make_kwargs(args)

    run_command(
        project,
        project.supply_config_file,
        kwargs["path_to_config"],
    )


supply_config_file_parser = subparsers.add_parser(
    "supply-config-file",
    aliases=["supply_config_file"],
    description=DataShuttle.supply_config_file.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
supply_config_file_parser.set_defaults(func=supply_config_file)

supply_config_file_parser.add_argument(
    "path_to_config",
    type=str,
    help="Required: (str, single or multiple)",
)

# ------------------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------------------


def main() -> None:
    """
    Get the arguments, initialise the datashuttle project
    and pass the project and arguments to default function.
    Note these functions must all accept two arguments. In the
    case where only project is required, *args is used
    (e.g. get_remote_path).

    Supress the warning that a config file must
    be made on project initialisation when
    a config is being made.
    """
    args = parser.parse_args()

    warn = (
        "ignore"
        if str(args.func.__name__) == "make_config_file"
        else "default"
    )

    warnings.filterwarnings(warn)  # type: ignore
    project = DataShuttle(args.project_name)
    warnings.filterwarnings("default")

    if len(vars(args)) > 1:
        args.func(project, args)
    else:
        print(
            f"Datashuttle project: {args.project_name}. "
            f"Add additional commands, see --help for details"
        )


if __name__ == "__main__":
    main()
