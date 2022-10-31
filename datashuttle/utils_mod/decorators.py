from functools import wraps

from datashuttle.utils_mod.utils import raise_error


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


def check_configs_set(func):
    """ """

    @wraps(func)
    def wrapper(*args, **kwargs):

        error_type = None

        if args[0].cfg is None:
            error_type = "configs"

        elif args[0].cfg["local_path"] is None:
            error_type = "local_path"

        elif (
            args[0].cfg["remote_path_local"] is None
            and args[0].cfg["remote_path_ssh"] is None
        ):
            error_type = "either remote_path_local or remote_path_ssh"

        elif args[0].cfg["ssh_to_remote"] is None:
            error_type = "ssh_to_remote"

        if error_type:
            raise_error(
                f"Must set {error_type} with make_config_file() "
                f"(or update_config()) before using this function"
            )
        else:
            return func(*args, **kwargs)

    return wrapper
