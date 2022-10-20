from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def remote_path():
    """ """
    remote_path = Path(
        r"Z:\manager\project_manager_tests"
    )  # Set remote path here

    if remote_path.name == "REMOTE PATH":
        pytest.fail(
            "[Test Setup Error]: remote_path is not set in conftest.py"
        )

    if not remote_path.exists():
        pytest.fail(
            "[Test Setup Error] remote_path (set in conftest.py) is not an existing directory."
        )

    is_empty = next(remote_path.iterdir(), True)

    if is_empty is not True:
        pytest.fail(
            "[Test Setup Error] remote_path (set in conftest.py) directory specified is not empty."
        )

    return remote_path
