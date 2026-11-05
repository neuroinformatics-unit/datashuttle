"""Single source of truth for release-artifact filenames.

Both the packaging scripts (which produce the installers uploaded to a GitHub
Release) and the docs build (``docs/source/conf.py``, which generates the
direct download links on the Install page) import these helpers. Keeping the
filename format in one place guarantees the release asset name and the
download link can never drift apart.

The ``version`` passed in must be the release version derived from the git tag
(via ``setuptools_scm`` / installed package metadata), so that on a tag push
``vX.Y.Z`` every consumer produces the identical string.
"""


def windows_installer_name(version: str) -> str:
    """Return the Windows installer filename for a given version."""
    return f"datashuttle_{version}.exe"


def windows_installer_stem(version: str) -> str:
    """Return the Windows installer filename without the ``.exe`` suffix.

    Inno Setup's ``OutputBaseFilename`` expects the stem, not the full name.
    """
    return f"datashuttle_{version}"


def macos_dmg_name(version: str, arch: str) -> str:
    """Return the macOS .dmg filename for a given version and architecture.

    ``arch`` is the target architecture as reported by the build matrix /
    ``platform.machine()`` (e.g. ``arm64`` or ``x86_64``).
    """
    return f"datashuttle-{version}-{arch}.dmg"
