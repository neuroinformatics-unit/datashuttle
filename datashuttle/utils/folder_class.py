class Folder:
    """Contains details of canonical folders in the project folder tree.

    see configs.canonical_folders.py for details.
    """

    def __init__(
        self,
        name: str,
        level: str,
    ):
        """Initialise the Folder class.

        Parameters
        ----------
        name
            the name of the folder.

        level
            level to make the folder at.

        """
        self.name = name
        self.level = level
