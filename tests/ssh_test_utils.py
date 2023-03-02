import builtins
import copy
import os
from pytest import ssh_config

from datashuttle.utils import rclone, ssh


def setup_project_for_ssh(
    project, remote_path, remote_host_id, remote_host_username
):
    """
    Setup the project configs to use SSH connection
    to remote
    """
    project.update_config(
        "remote_path",
        remote_path,
    )
    project.update_config("remote_host_id", remote_host_id)
    project.update_config("remote_host_username", remote_host_username)
    project.update_config("connection_method", "ssh")

    rclone.setup_remote_as_rclone_target(
        "ssh",
        project.cfg,
        project.cfg.get_rclone_config_name("ssh"),
        project.cfg.ssh_key_path,
    )


def get_password():
    """
    Load the password from file. Password is provided to NIU team
    members only.
    """
    test_ssh_script_path = os.path.dirname(os.path.realpath(__file__))
    with open(ssh_config.PASSWORD_FILE, "r") as file:
        password = file.readlines()[0]
    return password


def setup_mock_input(input_):
    """
    This is very similar to pytest monkeypatch but
    using that was giving me very strange output,
    monkeypatch.setattr('builtins.input', lambda _: "n")
    i.e. pdb went deep into some unrelated code stack
    """
    orig_builtin = copy.deepcopy(builtins.input)
    builtins.input = lambda _: input_  # type: ignore
    return orig_builtin


def restore_mock_input(orig_builtin):
    """
    orig_builtin: the copied, original builtins.input
    """
    builtins.input = orig_builtin


def setup_hostkeys(project):
    """
    Convenience function to verify the server hostkey.
    """
    orig_builtin = setup_mock_input(input_="y")
    ssh.verify_ssh_remote_host(
        project.cfg["remote_host_id"], project.cfg.hostkeys_path, log=True
    )
    restore_mock_input(orig_builtin)
