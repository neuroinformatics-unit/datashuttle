from typing import Any, Union

import click

from datashuttle.datashuttle import DataShuttle
from datashuttle.utils_mod import utils

# @click.option('--repo-home', envvar='REPO_HOME', default='.repo')
# @click.option('--debug/--no-debug', default=False,
#            envvar='REPO_DEBUG')


@click.group(invoke_without_command=True)
@click.argument("project_name")
@click.pass_context
def entry(ctx, project_name):
    """
    All Errors, Warnings will be propagated so no need to explicitly check at this level.
    TODO: underscores go to dashes
    TODO:
    """
    ctx.obj = DataShuttle(project_name)


@entry.command()
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
def make_config_file(ctx, local_path, ssh_to_remote, **kwargs):
    """
    think more about None
    """
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    ctx.obj.make_config_file(local_path, ssh_to_remote, *filtered_kwargs)


@entry.command()
@click.argument("option_key", type=str)
@click.argument("new_info")
@click.pass_context
def update_config(ctx, option_key, new_info):
    """ """
    if option_key in [
        "ssh_to_remote",  # this is not nice, need to find a way to type input depending on str value
        "use_ephys",
        "use_ephys_behav",  # TODO: also, it is still possible for users to input wrong type in update_configs
        "use_ephys_behav_camera",  # TODO: this is still not create because it is not clear that user input string
        "use_behav",
        "use_behav_camera",
        "use_imaging",
        "use_histology",
    ]:
        if new_info not in ["True", "False"]:
            utils.raise_error("Input value must be True or False")

        new_info = bool(new_info)

    ctx.obj.update_config(option_key, new_info)


@entry.command()
@click.pass_context
def get_local_path(ctx):
    click.echo(ctx.obj.get_local_path())


@entry.command()
@click.pass_context
def get_appdir_path(ctx):
    click.echo(ctx.obj.get_appdir_path())


@entry.command()
@click.pass_context
def get_config_path(ctx):
    click.echo(ctx.obj.get_config_path())


@entry.command()
@click.pass_context
def get_remote_path(ctx):
    click.echo(ctx.obj.get_remote_path())


"""
local_path,
ssh_to_remote,
remote_path_local,
remote_path_ssh,
remote_host_id,
remote_host_username,
sub_prefix, ses_prefix,
use_ephys,
use_ephys_behav,
use_ephys_behav_camera,
use_behav,
use_behav_camera,
use_imaging,
use_histology

remote_path_local: str = None,
remote_path_ssh: str = None,
remote_host_id: str = None,
remote_host_username: str = None,
sub_prefix: str = "sub-",
ses_prefix: str = "ses-",
use_ephys: bool = True,
use_ephys_behav: bool = True,
use_ephys_behav_camera: bool = True,
use_behav: bool = True,
use_behav_camera: bool = True,
use_imaging: bool = True,
use_histology: bool = True,
"""
"""
@click.group()
@click.pass_context
def entry(ctx, project_name):

    # ctx.obj =

    breakpoint()
"""
"""
@click.command()
@click.argument('filename')
@click.argument("command")
def entry(filename, command):
    Print FILENAME.
    click.echo(filename)
    click.echo(command)
"""
