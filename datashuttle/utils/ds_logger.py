from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path

    from datashuttle.configs.configs import Configs

import copy
import logging
from datetime import datetime

from fancylog import fancylog

import datashuttle as package_to_log
from datashuttle.utils import utils


def get_logger_name() -> str:
    """Return the name of the logger."""
    return "datashuttle"


def get_logger() -> Logger:
    """Return the instance of the logger object."""
    return logging.getLogger(get_logger_name())


def logging_is_active() -> bool:
    """Return a bool indicating if the logger is active."""
    logger_exists = get_logger_name() in logging.root.manager.loggerDict
    if logger_exists and get_logger().handlers != []:
        return True
    return False


def start(
    path_to_log: Path,
    command_name: str,
    variables: Optional[List[Any]],
    verbose: bool = True,
) -> None:
    """Call fancylog to initialise logging.

    Parameters
    ----------
    path_to_log
        Path to save the log file to.

    command_name
        Name of the datashuttle command run, which is included
        in the log filename.

    variables
        Local variables to log.

    verbose
        Verbosity passed to ``fancylog``.

    """
    filename = get_logging_filename(command_name)

    fancylog.start_logging(
        path_to_log,
        package_to_log,
        filename=filename,
        variables=variables,
        verbose=verbose,
        timestamp=False,
        file_log_level="DEBUG",
        write_git=True,
        log_to_console=False,
        logger_name=get_logger_name(),
    )
    logger = get_logger()
    logger.info(f"Starting logging for command {command_name}")


def get_logging_filename(command_name: str) -> str:
    """Return the log filename.

    This starts with ISO8601-formatted datetime, so logs
    are stored in datetime order.

    Parameters
    ----------
    command_name
        Name of the datashuttle command run, which is included
        in the log filename.

    """
    filename = datetime.now().strftime(f"%Y%m%dT%H%M%S_{command_name}")
    return filename


def log_names(list_of_headers: List[Any], list_of_names: List[Any]) -> None:
    """Log a list of subject or session names.

    Parameters
    ----------
    list_of_headers
        a list of titles that the names
        will be printed under, e.g. "sub_names", "ses_names"

    list_of_names
        list of names to print to log

    """
    for header, names in zip(list_of_headers, list_of_names):
        utils.log(f"{header}: {names}")


def wrap_variables_for_fancylog(local_vars: dict, cfg: Configs) -> List:
    """Wrap the locals from the original function call for fancylog.

    Fancylog will log these variables as well as the
    datashuttle.cfg in a wrapper class with __dict__
    attribute for fancylog writing.

    Delete the self attribute (which is DataShuttle class)
    to keep the logs neat, as it adds no information.

    Returns
    -------
    A list holding a wrapper class that holds all variable
    state for fancylog to log.

    """

    class VariablesState:
        def __init__(self, local_vars_, cfg_):
            local_vars_ = copy.deepcopy(local_vars_)
            del local_vars_["self"]
            self.locals = local_vars_
            self.cfg = copy.deepcopy(cfg_)

    variables = [VariablesState(local_vars, cfg)]

    return variables


def close_log_filehandler() -> None:
    """Remove handlers from all loggers."""
    logger = get_logger()
    logger.debug("Finished logging.")
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()
