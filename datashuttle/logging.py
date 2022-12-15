import fancylog as package
from fancylog import fancylog


def start(directory: str) -> None:
    """"""
    fancylog.start_logging(directory, package, verbose=True, timestamp=True)
