from functools import wraps
from typing import Optional

from datashuttle.utils.custom_exceptions import ConfigError
from datashuttle.utils.utils import log_and_raise_error


def requires_ssh_configs(func):
    """Check ssh configs have been set.

    Used on Mainwindow class methods only as first
    arg is assumed to be self (containing cfgs).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if (
            not args[0].cfg["central_host_id"]
            or not args[0].cfg["central_host_username"]
        ):
            log_and_raise_error(
                "Cannot setup SSH connection, 'central_host_id' "
                "or 'central_host_username' is not set in "
                "the configuration file.",
                ConfigError,
            )
        else:
            return func(*args, **kwargs)

    return wrapper


def requires_aws_configs(func):
    """Check Amazon Web Service configs have been set."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if (
            not args[0].cfg["aws_access_key_id"]
            or not args[0].cfg["aws_region"]
        ):
            log_and_raise_error(
                "Cannot setup AWS connection, 'aws_access_key_id' "
                "or 'aws_region' is not set in the "
                "configuration file",
                ConfigError,
            )

        else:
            return func(*args, **kwargs)

    return wrapper


def check_configs_set(func):
    """Check configs have been set."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].cfg is None:
            log_and_raise_error(
                "Must set configs with make_config_file() "
                "before using this function.",
                ConfigError,
            )
        else:
            return func(*args, **kwargs)

    return wrapper


def check_is_not_local_project(func):
    """Check that the project is not a local project.

    This decorator should be placed above methods which
    require `central_path` and `connection_method` to be set.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].is_local_project():
            log_and_raise_error(
                "This function cannot be used for a local-project. "
                "Set connection configurations using `update_config_file` "
                "to use this functionality.",
                ConfigError,
            )
        else:
            return func(*args, **kwargs)

    return wrapper


def with_logging(
    command_name: Optional[str] = None,
    store_in_temp_folder: bool = False,
    conditional_param: Optional[str] = None,
):
    """Automatically handle logging for DataShuttle methods.

    This decorator:
    1. Starts logging at the beginning of the function
    2. Captures local variables for logging
    3. Ensures logging is closed even if an exception occurs

    Parameters
    ----------
    command_name
        Name of the command for logging. If None, uses the function name
        with underscores replaced by hyphens.
    store_in_temp_folder
        If True, store logs in temp folder instead of project logging path.
    conditional_param
        Name of parameter that controls whether logging occurs (e.g., "log").
        If specified and that parameter is False, logging is skipped.

    Examples
    --------
    @check_configs_set
    @with_logging()
    def upload_rawdata(self, ...):
        ...

    @with_logging(conditional_param="log")
    def create_folders(self, ..., log: bool = True):
        ...

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect

            from datashuttle.utils import ds_logger

            # Get the DataShuttle instance (first argument)
            self = args[0]

            # Check if logging should be skipped based on conditional parameter
            if conditional_param:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                if not bound_args.arguments.get(conditional_param, True):
                    # Skip logging - just run the function
                    return func(*args, **kwargs)

            # Determine command name
            log_command_name = (
                command_name
                if command_name
                else func.__name__.replace("_", "-")
            )

            # Capture local variables for logging
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            local_vars = dict(bound_args.arguments)

            # Start logging
            self._start_log(
                log_command_name,
                local_vars=local_vars,
                store_in_temp_folder=store_in_temp_folder,
            )

            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            finally:
                # Always close logging, even if exception occurs
                ds_logger.close_log_filehandler()

        return wrapper

    return decorator
