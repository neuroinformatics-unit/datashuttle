from functools import wraps

from .utils import raise_error


def requires_ssh_configs(func):
    """
    Decorator to check file is loaded. Used on Mainwindow class
    methods only as first arg is assumed to be self (containing cfgs)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if (
            not args[0].cfg["remote_host_id"]
            or not args[0].cfg["remote_host_username"]
        ):
            raise_error(
                "Cannot setup SSH connection, configuration "
                "file remote_host_id or remote_host_username is not set."
            )
        else:
            return func(*args, **kwargs)

    return wrapper
