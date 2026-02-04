import builtins
import copy
import subprocess
import sys

from datashuttle.utils import utils


def setup_project_for_ssh(
    project,
):
    """
    Set up the project configs to use
    SSH connection to central. The settings
    set up a connection to the Dockerfile image
    found in /ssh_test_images.
    """
    project.update_config_file(
        connection_method="ssh",
        central_path=f"/home/sshuser/datashuttle/{project.project_name}",
        central_host_id="localhost",
        central_host_username="sshuser",
    )


def setup_ssh_connection(project):
    """
    Convenience function to verify the server hostkey and ssh
    key pairs to the Dockerfile image for ssh tests.

    This requires monkeypatching a number of functions involved
    in the SSH setup process. `input()` is patched to always
    return the required hostkey confirmation "y". `getpass()` is
    patched to always return the password for the container in which
    SSH tests are run. `isatty()` is patched because when running this
    for some reason it appears to be in a TTY - this might be a
    container thing.
    """
    # Monkeypatch
    orig_input = copy.deepcopy(builtins.input)
    builtins.input = lambda _: "y"  # type: ignore

    orig_get_secret = copy.deepcopy(utils.get_connection_secret_from_user)
    utils.get_connection_secret_from_user = lambda *args, **kwargs: "password"  # type: ignore

    orig_isatty = copy.deepcopy(sys.stdin.isatty)
    sys.stdin.isatty = lambda: True

    try:
        project.setup_ssh_connection()
    finally:
        # Restore functions
        builtins.input = orig_input
        utils.get_connection_secret_from_user = orig_get_secret
        sys.stdin.isatty = orig_isatty


def docker_is_running():
    if not is_docker_installed():
        return False

    is_running = check_sys_command_returns_0("docker stats --no-stream")
    return is_running


def is_docker_installed():
    return check_sys_command_returns_0("docker -v")


def check_sys_command_returns_0(command):
    return (
        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
