import argparse

import simplejson

from datashuttle.datashuttle import DataShuttle
from datashuttle.utils_mod import utils

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"


# ------------------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------------------


def run_command(project, function, *args, **kwargs):
    """
    If project is protected test name, dump the variables to
    stdout so they can be checked. Otherwise, run the
    DataShuttle function.
    """
    if project.project_name == PROTECTED_TEST_PROJECT_NAME:
        print("TEST_OUT_START: ", simplejson.dumps([args, kwargs]))
    else:
        function(*args, **kwargs)


def make_kwargs(args):
    kwargs = vars(args)
    del kwargs["func"]
    del kwargs["project_name"]
    return kwargs


def handle_bool(key, value):
    if key in [
        "ssh_to_remote",
        "use_ephys",
        "use_ephys_behav",
        "use_ephys_behav_camera",
        "use_behav",
        "use_behav_camera",
        "use_imaging",
        "use_histology",
    ]:
        if value is not None and value not in [
            "True",
            "False",
            "true",
            "false",
        ]:
            utils.raise_error("Input value must be True or False")

        value = value in ["True", "true"]

    elif value in ["None", "none"]:
        value = None

    return value


def handle_kwargs_bools(kwargs):
    """"""
    for key in kwargs.keys():
        kwargs[key] = handle_bool(key, kwargs[key])
    return kwargs


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
    "\ntype python -m datashuttle [PROJECT NAME] [COMMAND] --help'"
    "\n\n"
    "On first use it is necessary to setup configurations. \ne.g."
    "'python -m datashuttle [PROJECT NAME] make_config_file [OPTIONS]'"
    "\n\n"
    "see \n'python -m datashuttle <project_name> make_config_file --help'"
    "\nfor full list of options."
    "\n\n"
    "All command and argument names are matched to the API "
    "documentation. "
    "\n\n"
    "----------------------------------------------------------------------"
)

parser = argparse.ArgumentParser(
    prog="datashuttle",
    usage="%(prog)s [PROJECT NAME]",
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


def make_config_file(project, args):
    kwargs = make_kwargs(args)
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    filtered_kwargs = handle_kwargs_bools(filtered_kwargs)

    run_command(
        project,
        project.make_config_file,
        **filtered_kwargs,
    )


make_config_file_parser = subparsers.add_parser(
    "make_config_file",
    description=DataShuttle.make_config_file.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
make_config_file_parser.set_defaults(func=make_config_file)

make_config_file_parser.add_argument(
    "local_path", type=str, help="Required: (str)"
)

make_config_file_parser = make_config_file_parser.add_argument_group(
    "named arguments:"
)  # type: ignore
make_config_file_parser.add_argument(
    "--ssh_to_remote",
    required=False,
    default=None,
    action="store",
    help="flag (default False)",
)
make_config_file_parser.add_argument(
    "--remote_path_local",
    required=False,
    type=str,
    help="This or --remote_path_ssh must be set(str)",
    metavar="",
)
make_config_file_parser.add_argument(
    "--remote_path_ssh",
    required=False,
    type=str,
    help="This or --remote_path_local must be set(str)",
    metavar="",
)
make_config_file_parser.add_argument(
    "--remote_host_id",
    required=False,
    type=str,
    help="(str)",
    metavar="",
)
make_config_file_parser.add_argument(
    "--remote_host_username", required=False, help="(str)", metavar=""
)
make_config_file_parser.add_argument(
    "--use_ephys",
    required=False,
    default=None,
    action="store",
    help="flag (default False)",
)
make_config_file_parser.add_argument(
    "--use_behav",
    required=False,
    default=None,
    action="store",
    help="flag (default False)",
)
make_config_file_parser.add_argument(
    "--use_imaging",
    required=False,
    default=None,
    action="store",
    help="flag (default False)",
)
make_config_file_parser.add_argument(
    "--use_histology",
    required=False,
    default=None,
    action="store",
    help="flag (default False)",
)


# ------------------------------------------------------------------------------------------
# Update Config
# ------------------------------------------------------------------------------------------


def update_config(project, args):
    """"""
    kwargs = make_kwargs(args)
    option_key = kwargs["option_key"]
    new_info = kwargs["new_info"]

    new_info = handle_bool(option_key, new_info)

    run_command(
        project,
        project.update_config,
        option_key,
        new_info,
    )


make_config_file_parser = subparsers.add_parser(
    "update_config",
    description=DataShuttle.update_config.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
make_config_file_parser.set_defaults(func=update_config)

make_config_file_parser.add_argument(
    "option_key",
    action="store",
    help="(str) (see make_config_file --help",
)
make_config_file_parser.add_argument(
    "new_info", action="store", help="(str or bool) depending on option key"
)


# ------------------------------------------------------------------------------------------
# Setup SSH
# ------------------------------------------------------------------------------------------


def setup_ssh_connection_to_remote_server(project, args):
    project.setup_ssh_connection_to_remote_server()


setup_ssh_connection_to_remote_server_parser = subparsers.add_parser(
    "setup_ssh_connection_to_remote_server",
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


def make_sub_dir(project, args):
    """"""
    kwargs = make_kwargs(args)

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(project, project.make_sub_dir, **filtered_kwargs)


make_sub_dir_parser = subparsers.add_parser(
    "make_sub_dir",
    description=DataShuttle.make_sub_dir.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
make_sub_dir_parser = make_sub_dir_parser.add_argument_group(
    "named arguments:"
)  # type: ignore
make_sub_dir_parser.set_defaults(func=make_sub_dir)

make_sub_dir_parser.add_argument(
    "--sub_names",
    type=str,
    nargs="+",
    required=True,
    help="Required: (str, single or multiple) (selection of data types, or 'all')",
    metavar="",
)
make_sub_dir_parser.add_argument(
    "--ses_names",
    nargs="+",
    type=str,
    required=False,
    help="Optional: (str, single or multiple) (selection of data types, or 'all')",
    metavar="",
)
make_sub_dir_parser.add_argument(
    "--experiment_type",
    type=str,
    nargs="+",
    required=True,
    help="Required: (str, single or multiple) (selection of data types, or 'all') (default 'all')",
    metavar="",
)

# ------------------------------------------------------------------------------------------
# Transfer
# ------------------------------------------------------------------------------------------

# Upload Data --------------------------------------------------------------------------


def upload_data(project, args):
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.upload_data,
        **kwargs,
    )


upload_data_parser = subparsers.add_parser(
    "upload_data",
    description=DataShuttle.upload_data.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
upload_data_parser = upload_data_parser.add_argument_group(
    "named arguments:"
)  # type: ignore
upload_data_parser.set_defaults(func=upload_data)

upload_data_parser.add_argument(
    "--sub_names",
    type=str,
    nargs="+",
    required=True,
    help="Required: (str, single or multiple)",
    metavar="",
)
upload_data_parser.add_argument(
    "--ses_names",
    type=str,
    nargs="+",
    required=True,
    help="Required: (str, single or multiple)",
    metavar="",
)
upload_data_parser.add_argument(
    "--experiment_type",
    type=str,
    nargs="+",
    required=False,
    help="Optional: (str, single or multiple) (selection of data types, or 'all') (default 'all')",
    metavar="",
)
upload_data_parser.add_argument(
    "--preview",
    required=False,
    action="store_true",
    help="Optional: flag (default False)",
)


# Download Data --------------------------------------------------------------------------


def download_data(project, args):
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.download_data,
        **kwargs,
    )


download_data_parser = subparsers.add_parser(
    "download_data",
    description=DataShuttle.download_data.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
download_data_parser = download_data_parser.add_argument_group(
    "named arguments:"  # type: ignore
)
download_data_parser.set_defaults(func=download_data)

download_data_parser.add_argument(
    "--sub_names",
    type=str,
    nargs="+",
    required=True,
    help="Required: (str, single or multiple)",
    metavar="",
)
download_data_parser.add_argument(
    "--ses_names",
    type=str,
    nargs="+",
    required=True,
    help="Required: (str, single or multiple)",
    metavar="",
)
download_data_parser.add_argument(
    "--experiment_type",
    type=str,
    nargs="+",
    required=False,
    help="Optional: (str or list) (selection of data types, or 'all') (default 'all')",
    metavar="",
)
download_data_parser.add_argument(
    "--preview",
    required=False,
    action="store_true",
    help="Optional: flag (default False)",
)


# Upload Project Dir or File -----------------------------------------------------------


def upload_project_dir_or_file(project, args):
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.upload_project_dir_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


upload_project_dir_or_file_parser = subparsers.add_parser(
    "upload_project_dir_or_file",
    description=DataShuttle.upload_project_dir_or_file.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
upload_project_dir_or_file_parser.set_defaults(func=upload_project_dir_or_file)

upload_project_dir_or_file_parser.add_argument(
    "filepath", type=str, help="Required: (str)"
)
upload_project_dir_or_file_parser.add_argument(
    "--preview", action="store_true", help="flag (default False)"
)


# Download Project Dir or File ---------------------------------------------------------


def download_project_dir_or_file(project, args):
    """"""
    kwargs = make_kwargs(args)

    run_command(
        project,
        project.download_project_dir_or_file,
        kwargs.pop("filepath"),
        **kwargs,
    )


download_project_dir_or_file_parser = subparsers.add_parser(
    "download_project_dir_or_file",
    description=DataShuttle.download_project_dir_or_file.__doc__,
    formatter_class=argparse.RawTextHelpFormatter,
    help="",
)
download_project_dir_or_file_parser.set_defaults(
    func=download_project_dir_or_file
)

download_project_dir_or_file_parser.add_argument(
    "filepath", type=str, help="Required: (str)"
)
download_project_dir_or_file_parser.add_argument(
    "--preview", action="store_true", help="flag (default False)"
)


# ------------------------------------------------------------------------------------------
# Getters
# ------------------------------------------------------------------------------------------
# Almost worth creating a function factory for these, only thing that changes is
# DataShuttle function. But code would be hard to understand and only 4 cases...

# Get Local Path --------------------------------------------------------------------------


def get_local_path(project, args):
    """"""
    print(project.get_local_path())


get_local_path_parser = subparsers.add_parser(
    "get_local_path",
    description=DataShuttle.get_local_path.__doc__,
)
get_local_path_parser.set_defaults(func=get_local_path)


# Get Appdir Path --------------------------------------------------------------------------


def get_appdir_path(project, args):
    """"""
    print(project.get_appdir_path())


get_appdir_path_parser = subparsers.add_parser(
    "get_appdir_path",
    description=DataShuttle.get_appdir_path.__doc__,
)
get_appdir_path_parser.set_defaults(func=get_appdir_path)


# Get Config Path --------------------------------------------------------------------------


def get_config_path(project, args):
    """"""
    print(project.get_config_path())


get_config_path_parser = subparsers.add_parser(
    "get_config_path",
    description=DataShuttle.get_config_path.__doc__,
)
get_config_path_parser.set_defaults(func=get_config_path)


# Get Remote Path --------------------------------------------------------------------------


def get_remote_path(project, args):
    """"""
    print(project.get_remote_path())


get_remote_path_parser = subparsers.add_parser(
    "get_remote_path",
    description=DataShuttle.get_remote_path.__doc__,
)
get_remote_path_parser.set_defaults(func=get_remote_path)


# Show Configs --------------------------------------------------------------------------


def show_configs(project, args):
    """"""
    project.show_configs()


show_configs_parser = subparsers.add_parser(
    "show_configs",
    description=DataShuttle.show_configs.__doc__,
)
show_configs_parser.set_defaults(func=show_configs)

# ------------------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------------------


def main():
    args = parser.parse_args()
    project = DataShuttle(args.project_name)

    if len(vars(args)) > 1:
        args.func(project, args)
    else:
        print(
            f"Datashuttle project: {args.project_name}. Add additional commands, see --help for details"
        )


if __name__ == "__main__":
    main()
