class Directory:
    """
    Directory class used to contain details of canonical
    directories in the project directory tree.
    """

    def __init__(self, name, used, subdirs=None):
        self.name = name
        self.used = used
        self.subdirs = subdirs
