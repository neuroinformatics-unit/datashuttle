import argparse
import sys

import simplejson

from datashuttle.datashuttle import DataShuttle
from datashuttle.utils_mod import utils

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"

# ------------------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------------------


def run_command(PROJECT, function, *args, **kwargs):
    """"""
    if PROJECT.project_name == PROTECTED_TEST_PROJECT_NAME:
        print("TEST_OUT_START: ", simplejson.dumps([args, kwargs]))
    else:
        breakpoint()
        function(*args, **kwargs)


def make_kwargs(args):
    kwargs = vars(args)
    del kwargs["func"]
    del kwargs["project_name"]
    return kwargs


# ------------------------------------------------------------------------------------------
# Entry
# ------------------------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    prog="datashuttle",
    usage="%(prog)s [PROJECT NAME] [COMMAND] [OPTIONS]",
    description="PLACEHOLDER DESCRIPTION",
)  # TODO: check aginst parserck

project_name_argument = parser.add_argument(dest="project_name")
subparsers = parser.add_subparsers()

# ------------------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------------------


def make_config_file(args):

    kwargs = make_kwargs(args)
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(
        PROJECT,
        PROJECT.make_config_file,
        **filtered_kwargs,
    )


make_config_file_parser = subparsers.add_parser(
    "make_config_file", usage=DataShuttle.make_config_file.__doc__
)
make_config_file_parser.set_defaults(func=make_config_file)

make_config_file_parser.add_argument("--local_path", required=True, type=str)
make_config_file_parser.add_argument(
    "--ssh_to_remote", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--remote_path_local", required=False, type=str
)
make_config_file_parser.add_argument(
    "--remote_path_ssh", required=False, type=str
)
make_config_file_parser.add_argument(
    "--remote_host_id", required=False, type=str
)
make_config_file_parser.add_argument("--remote_host_username", required=False)
make_config_file_parser.add_argument("--sub_prefix", required=False, type=str)
make_config_file_parser.add_argument("--ses_prefix", required=False, type=str)
make_config_file_parser.add_argument(
    "--use_ephys", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--use_ephys_behav", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--use_ephys_behav_camera", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--use_behav", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--use_behav_camera", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--use_imaging", required=False, action="store_true"
)
make_config_file_parser.add_argument(
    "--use_histology", required=False, action="store_true"
)


# ------------------------------------------------------------------------------------------
# Update Config
# ------------------------------------------------------------------------------------------


def update_config(args):
    """"""
    kwargs = make_kwargs(args)
    option_key = kwargs["option_key"]
    new_info = kwargs["new_info"]

    if new_info == "None":
        new_info = None

    if option_key in [
        "ssh_to_remote",
        "use_ephys",
        "use_ephys_behav",
        "use_ephys_behav_camera",
        "use_behav",
        "use_behav_camera",
        "use_imaging",
        "use_histology",
    ]:
        if new_info not in ["True", "False", "true", "false"]:
            utils.raise_error("Input value must be True or False")

        new_info = new_info in ["True", "true"]

    run_command(
        PROJECT,
        PROJECT.update_config,
        option_key,
        new_info,
    )


make_config_file_parser = subparsers.add_parser(
    "update_config", usage=DataShuttle.update_config.__doc__
)
make_config_file_parser.set_defaults(func=update_config)

make_config_file_parser.add_argument("option_key", action="store")
make_config_file_parser.add_argument("new_info", action="store")

# ------------------------------------------------------------------------------------------
# Setup SSH
# ------------------------------------------------------------------------------------------


def setup_ssh_connection_to_remote_server(args):
    PROJECT.setup_ssh_connection_to_remote_server()


setup_ssh_connection_to_remote_server_parser = subparsers.add_parser(
    "setup_ssh_connection_to_remote_server",
    usage=DataShuttle.setup_ssh_connection_to_remote_server.__doc__,
)
setup_ssh_connection_to_remote_server_parser.set_defaults(
    func=setup_ssh_connection_to_remote_server
)

# ------------------------------------------------------------------------------------------
# Make Sub Dirs
# ------------------------------------------------------------------------------------------


def make_sub_dir(args):  # TODO: fix doc! wrong!
    """
    FOR CLI INPUT: To input a list of strings
    (to --experiment_type, --sub_names, --ses_names),
    use the reserved "<>" syntax. Everything between
    "<>" will be assumed to be a list of string with
    elements separated by commas.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    kwargs = make_kwargs(args)

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(PROJECT, PROJECT.make_sub_dir, **filtered_kwargs)


make_sub_dir_parser = subparsers.add_parser(
    "make_sub_dir", usage=DataShuttle.make_sub_dir.__doc__
)
make_sub_dir_parser.set_defaults(func=make_sub_dir)

make_sub_dir_parser.add_argument(
    "--experiment_type", type=str, nargs="+", required=True
)
make_sub_dir_parser.add_argument(
    "--sub_names", type=str, nargs="+", required=True
)
make_sub_dir_parser.add_argument("--ses_names", type=str, required=False)
make_sub_dir_parser.add_argument(
    "--make_ses_tree", type=bool, required=False
)  # TODO: flip this to match

# ------------------------------------------------------------------------------------------
# Transfer
# ------------------------------------------------------------------------------------------

# Upload Data --------------------------------------------------------------------------


def upload_data(args):
    """
    FOR CLI INPUT: To input a list of strings
    (to --experiment_type, --sub_names, --ses_names),
    use the reserved "<>" syntax. Everything between
    "<>" will be assumed to be a list of string with
    elements separated by commas.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    kwargs = make_kwargs(args)

    run_command(
        PROJECT,  # TODO: dont need to pass this its global
        PROJECT.upload_data,
        **kwargs,
    )


upload_data_parser = subparsers.add_parser(
    "upload_data", usage=DataShuttle.upload_data.__doc__
)
upload_data_parser.set_defaults(func=upload_data)

upload_data_parser.add_argument(
    "--experiment_type", type=str, nargs="+", required=True
)
upload_data_parser.add_argument(
    "--sub_names", type=str, nargs="+", required=True
)
upload_data_parser.add_argument(
    "--ses_names", type=str, nargs="+", required=True
)
upload_data_parser.add_argument(
    "--preview", required=False, action="store_true"
)

# Download Data --------------------------------------------------------------------------


def download_data(args):  # TODO: FIX DOC!
    """
    FOR CLI INPUT: To input a list of strings
    (to --experiment_type, --sub_names, --ses_names),
    use the reserved "<>" syntax. Everything between
    "<>" will be assumed to be a list of string with
    elements separated by commas.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    kwargs = make_kwargs(args)

    run_command(
        PROJECT,  # TODO: dont need to pass this its global
        PROJECT.download_data,
        **kwargs,
    )


download_data_parser = subparsers.add_parser(
    "download_data", usage=DataShuttle.download_data.__doc__
)
download_data_parser.set_defaults(func=download_data)

download_data_parser.add_argument(
    "--experiment_type", type=str, nargs="+", required=True
)
download_data_parser.add_argument(
    "--sub_names", type=str, nargs="+", required=True
)
download_data_parser.add_argument(
    "--ses_names", type=str, nargs="+", required=True
)
download_data_parser.add_argument(
    "--preview", required=False, action="store_true"
)

# Upload Project Dir or File -----------------------------------------------------------


def upload_project_dir_or_file(args):
    """"""
    kwargs = make_kwargs(args)

    run_command(PROJECT, PROJECT.upload_project_dir_or_file, **kwargs)


upload_project_dir_or_file_parser = subparsers.add_parser(
    "upload_project_dir_or_file",
    usage=DataShuttle.upload_project_dir_or_file.__doc__,
)
upload_project_dir_or_file_parser.set_defaults(func=upload_project_dir_or_file)

upload_project_dir_or_file_parser.add_argument("filepath", type=str)
upload_project_dir_or_file_parser.add_argument(
    "--preview", action="store_true"
)

# Download Project Dir or File ---------------------------------------------------------


def download_project_dir_or_file(args):
    """"""
    kwargs = make_kwargs(args)

    run_command(PROJECT, PROJECT.download_project_dir_or_file, **kwargs)


download_project_dir_or_file_parser = subparsers.add_parser(
    "download_project_dir_or_file",
    usage=DataShuttle.download_project_dir_or_file.__doc__,
)
download_project_dir_or_file_parser.set_defaults(
    func=download_project_dir_or_file
)

download_project_dir_or_file_parser.add_argument("filepath", type=str)
download_project_dir_or_file_parser.add_argument(
    "--preview", action="store_true"
)

# ------------------------------------------------------------------------------------------
# Getters
# ------------------------------------------------------------------------------------------
# Almost worth creating a function factory for these, only thing that changes is
# DataShuttle function. But code would be hard to understand and only 4 cases...

# Get Local Path --------------------------------------------------------------------------


def get_local_path(args):
    """"""
    print(PROJECT.get_local_path())


get_local_path_parser = subparsers.add_parser(
    "get_local_path", usage=DataShuttle.get_local_path.__doc__
)
get_local_path_parser.set_defaults(func=get_local_path)

# Get Appdir Path --------------------------------------------------------------------------


def get_appdir_path(args):
    """"""
    print(PROJECT.get_appdir_path())


get_appdir_path_parser = subparsers.add_parser(
    "get_appdir_path", usage=DataShuttle.get_appdir_path.__doc__
)
get_appdir_path_parser.set_defaults(func=get_appdir_path)

# Get Config Path --------------------------------------------------------------------------


def get_config_path(args):
    """"""
    print(PROJECT.get_config_path())


get_config_path_parser = subparsers.add_parser(
    "get_config_path", usage=DataShuttle.get_config_path.__doc__
)
get_config_path_parser.set_defaults(func=get_config_path)

# Get Remote Path --------------------------------------------------------------------------


def get_remote_path(args):
    """"""
    print(PROJECT.get_remote_path())


get_remote_path_parser = subparsers.add_parser(
    "get_remote_path", usage=DataShuttle.get_remote_path.__doc__
)
get_remote_path_parser.set_defaults(func=get_remote_path)

# Show Configs --------------------------------------------------------------------------


def show_configs(args):
    """"""
    PROJECT.show_configs()


show_configs_parser = subparsers.add_parser(
    "show_configs", usage=DataShuttle.show_configs.__doc__
)
show_configs_parser.set_defaults(func=show_configs)

# ------------------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------------------

args = parser.parse_args()
PROJECT = DataShuttle(args.project_name)
PROJECT.run_as_test = args.project_name == PROTECTED_TEST_PROJECT_NAME
args.func(args)
