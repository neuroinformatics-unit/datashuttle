from functools import wraps

from datashuttle.utils import rclone, utils
from datashuttle.utils.custom_exceptions import ConfigError


def requires_ssh_configs(func):
    """
    Decorator to check file is loaded. Used on Mainwindow class
    methods only as first arg is assumed to be self (containing cfgs)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if (
            not args[0].cfg["central_host_id"]
            or not args[0].cfg["central_host_username"]
        ):
            utils.log_and_raise_error(
                "Cannot setup SSH connection, 'central_host_id' "
                "or 'central_host_username' is not set in "
                "the configuration file.",
                ConfigError,
            )
        else:
            return func(*args, **kwargs)

    return wrapper


def check_configs_set(func):
    """
    Check that configs have been loaded (i.e.
    project.cfg is not None) before the
    func is run.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].cfg is None:

            rclone.raise_prompt_rclone_download_if_does_not_exist()

            utils.log_and_raise_error(
                "Must set configs with make_config_file() "
                "before using this function.",
                ConfigError,
            )
        else:
            return func(*args, **kwargs)

    return wrapper


def check_is_not_local_project(func):
    """
    Decorator to check that the project is not
    a local project. If it is, raise.

    This decorator should be placed above methods which
    require `central_path` and `connection_method` to be set.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].is_local_project():
            utils.log_and_raise_error(
                "This function cannot be used for a local-project. "
                "Set connection configurations using `update_config_file` "
                "to use this functionality.",
                ConfigError,
            )
        else:
            return func(*args, **kwargs)

    return wrapper
