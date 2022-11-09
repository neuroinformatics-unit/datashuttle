"""
Setup the CLI for DataShuttle. Uses Click to wrap API arguments
and decorator to inherit the API function docstring, which are
used as --help arguments.
"""

from functools import wraps

import click
import simplejson

from datashuttle.datashuttle import DataShuttle
from datashuttle.utils_mod import utils

PROTECTED_TEST_PROJECT_NAME = "ds_protected_test_name"

# ------------------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------------------


def convert_none_from_str_to_nonetype(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        for key, value in kwargs.items():
            if value == "None":
                kwargs[key] = None

        return func(*args, **kwargs)

    return wrapper


def inherit_docstring_from_subfunction(func):
    """
    Take the docstring from the sub-function (i.e.
    the API function of the same name) and set the
    docstring of the CLI command to it.
    """
    subfunction_docstring = getattr(DataShuttle, func.__name__).__doc__
    new_dostring = "\n".join([subfunction_docstring, func.__doc__])

    setattr(func, "__doc__", new_dostring)
    return func


def handle_sub_ses_names_list(names):
    """
    Process list input. Because CLI inputs must be
    str or some other low-levle type (e.g. bool, int)
    to minic list of strings use a resevered <> syntax.

    Everything between "<>", with space in the middle,
    will be converted to list.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    if names.strip()[0] == "<" and names.strip()[-1] == ">":
        names_list = names.strip()[1:-1].split(",")
        names_list = [
            ele.strip() for ele in names_list
        ]  # TODO: assumes no leading or ending " " of sub / ses names
    else:
        names_list = [names]
    return names_list


# ------------------------------------------------------------------------------------------
# Entry
# ------------------------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.argument("project_name")
@click.pass_context
def entry(ctx, project_name):
    """
    DataShuttle command line interface. To get detailed help for
    commands, type 'python -m datashuttle <project_name> <command_name> --help'

    On first use it is necessary to setup configurations. e.g.
    'python -m datashuttle <project_name> make_config_file [args] [kwargs]'

    see 'python -m datashuttle <project_name> make_config_file --help'
    for arguments.

    All command and argument names are matched exactly to the API /
    documentation. To pass a list of strings as sub_names or ses_names,
    use "<>" to start/end the list and seperate all elements with a comma.
    This reserved syntax will be recognised and all strings separated by
    a comma will be used as distinct elements.
    """
    ctx.obj = DataShuttle(project_name)
    ctx.obj.run_as_test = project_name == PROTECTED_TEST_PROJECT_NAME


# ------------------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------------------


def run_command(ctx, function, *args, **kwargs):
    """"""
    if ctx.obj.run_as_test:
        print("TEST_OUT_START: ", simplejson.dumps([args, kwargs]))
    else:
        function(*args, **kwargs)


@entry.command("make_config_file")
@click.option("--local_path", required=True, type=str)
@click.option("--ssh_to_remote", required=True, type=bool)
@click.option("--remote_path_local", required=False, type=str)
@click.option("--remote_path_ssh", required=False, type=str)
@click.option("--remote_host_id", required=False, type=str)
@click.option("--remote_host_username", required=False)
@click.option("--sub_prefix", required=False, type=str)
@click.option("--ses_prefix", required=False, type=str)
@click.option("--use_ephys", required=False, type=bool)
@click.option("--use_ephys_behav", required=False, type=bool)
@click.option("--use_ephys_behav_camera", required=False, type=bool)
@click.option("--use_behav", required=False, type=bool)
@click.option("--use_behav_camera", required=False, type=bool)
@click.option("--use_imaging", required=False, type=bool)
@click.option("--use_histology", required=False, type=bool)
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def make_config_file(ctx, local_path, ssh_to_remote, **kwargs):
    """"""
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(
        ctx,
        ctx.obj.make_config_file,
        local_path,
        ssh_to_remote,
        **filtered_kwargs,
    )


@entry.command("update_config")
@click.argument("option_key", type=str)
@click.argument("new_info")
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def update_config(ctx, option_key, new_info):
    """"""
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

    run_command(ctx, ctx.obj.update_config, option_key, new_info)


@entry.command("setup_ssh_connection_to_remote_server")
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def setup_ssh_connection_to_remote_server(ctx):
    """"""
    ctx.obj.setup_ssh_connection_to_remote_server()


# ------------------------------------------------------------------------------------------
# Make Dirs
# ------------------------------------------------------------------------------------------


@entry.command("make_sub_dir")
@click.option("--experiment_type", type=str, required=True)
@click.option("--sub_names", type=str, required=True)
@click.option("--ses_names", type=str, required=False)
@click.option("--dont_make_ses_tree", type=bool, required=False)
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def make_sub_dir(ctx, experiment_type, sub_names, **kwargs):
    """
    FOR CLI INPUT: To input a list of strings
    (to --experiment_type, --sub_names, --ses_names),
    use the reserved "<>" syntax. Everything between
    "<>" will be assumed to be a list of string with
    elements separated by commas.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    experiment_type = handle_sub_ses_names_list(experiment_type)
    sub_names = handle_sub_ses_names_list(sub_names)

    if kwargs["ses_names"] is not None:
        kwargs["ses_names"] = handle_sub_ses_names_list(kwargs["ses_names"])

    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    run_command(
        ctx,
        ctx.obj.make_sub_dir,
        experiment_type,
        sub_names,
        **filtered_kwargs,
    )


# ------------------------------------------------------------------------------------------
# Transfer
# ------------------------------------------------------------------------------------------


@entry.command("upload_data")
@click.option("--experiment_type", type=str, required=True)
@click.option("--sub_names", type=str, required=True)
@click.option("--ses_names", type=str, required=True)
@click.option("--preview", is_flag=True)
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def upload_data(ctx, experiment_type, sub_names, ses_names, preview):
    """
    FOR CLI INPUT: To input a list of strings
    (to --experiment_type, --sub_names, --ses_names),
    use the reserved "<>" syntax. Everything between
    "<>" will be assumed to be a list of string with
    elements separated by commas.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    experiment_type = handle_sub_ses_names_list(experiment_type)
    sub_names = handle_sub_ses_names_list(sub_names)
    ses_names = handle_sub_ses_names_list(ses_names)

    run_command(
        ctx,
        ctx.obj.upload_data,
        experiment_type,
        sub_names,
        ses_names,
        preview,
    )


@entry.command("download_data")
@click.option("--experiment_type", type=str, required=True)
@click.option("--sub_names", type=str, required=True)
@click.option("--ses_names", type=str, required=True)
@click.option("--preview", is_flag=True)
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def download_data(ctx, experiment_type, sub_names, ses_names, preview):
    """
    FOR CLI INPUT: To input a list of strings
    (to --experiment_type, --sub_names, --ses_names),
    use the reserved "<>" syntax. Everything between
    "<>" will be assumed to be a list of string with
    elements separated by commas.

    e.g. "<one two three>" = ["one", "two", "three"]
    """
    experiment_type = handle_sub_ses_names_list(experiment_type)
    sub_names = handle_sub_ses_names_list(sub_names)
    ses_names = handle_sub_ses_names_list(ses_names)

    run_command(
        ctx,
        ctx.obj.download_data,
        experiment_type,
        sub_names,
        ses_names,
        preview,
    )


@entry.command("upload_project_dir_or_file")
@click.argument("filepath", type=str, required=True)
@click.option("--preview", is_flag=True)
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def upload_project_dir_or_file(ctx, filepath, preview):
    """"""
    run_command(ctx, ctx.obj.upload_project_dir_or_file, filepath, preview)


@entry.command("download_project_dir_or_file")
@click.argument("filepath", type=str, required=True)
@click.option("--preview", is_flag=True)
@click.pass_context
@inherit_docstring_from_subfunction
@convert_none_from_str_to_nonetype
def download_project_dir_or_file(ctx, filepath, preview):
    """"""
    run_command(ctx, ctx.obj.download_project_dir_or_file, filepath, preview)


# ------------------------------------------------------------------------------------------
# Getters
# ------------------------------------------------------------------------------------------


@entry.command("get_local_path")
@click.pass_context
@inherit_docstring_from_subfunction
def get_local_path(ctx):
    """"""
    click.echo(ctx.obj.get_local_path())


@entry.command("get_appdir_path")
@click.pass_context
@inherit_docstring_from_subfunction
def get_appdir_path(ctx):
    """"""
    click.echo(ctx.obj.get_appdir_path())


@entry.command("get_config_path")
@click.pass_context
@inherit_docstring_from_subfunction
def get_config_path(ctx):
    """"""
    click.echo(ctx.obj.get_config_path())


@entry.command("get_remote_path")
@click.pass_context
@inherit_docstring_from_subfunction
def get_remote_path(ctx):
    """"""
    click.echo(ctx.obj.get_remote_path())


@entry.command("show_configs")
@click.pass_context
@inherit_docstring_from_subfunction
def show_configs(ctx):
    """"""
    click.echo(ctx.obj.show_configs())
