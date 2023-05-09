class Directory:
    """
    Directory class used to contain details of canonical
    directories in the project folder tree.

    see configs.canonical_directories.py for details.
    """

    def __init__(
        self,
        name: str,
        used: bool,
        level: str,
    ):
        self.name = name
        self.used = used
        self.level = level
