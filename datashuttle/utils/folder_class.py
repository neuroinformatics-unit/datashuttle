class Folder:
    """
    Folder class used to contain details of canonical
    folders in the project folder tree.

    see configs.canonical_folders.py for details.
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
