import builtins
import copy

from datashuttle.utils import rclone, ssh


def setup_project_for_ssh(
    project, central_path, central_host_id, central_host_username
):
    """
    Set up the project configs to use SSH connection
    to central
    """
    project.update_config_file(
        central_path=central_path,
    )
    project.update_config_file(central_host_id=central_host_id)
    project.update_config_file(central_host_username=central_host_username)
    project.update_config_file(connection_method="ssh")

    rclone.setup_rclone_config_for_ssh(
        project.cfg,
        project.cfg.get_rclone_config_name("ssh"),
        project.cfg.ssh_key_path,
    )


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
    ssh.verify_ssh_central_host(
        project.cfg["central_host_id"], project.cfg.hostkeys_path, log=True
    )
    restore_mock_input(orig_builtin)
