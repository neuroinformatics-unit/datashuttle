import glob
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import List

import pytest

from datashuttle.utils.folders import search_for_wildcards


# Dummy implementation for canonical_tags
class DummyCanonicalTags:
    @staticmethod
    def tags(x: str) -> str:
        if x == "*":
            return "@*@"
        return x


# Patch canonical_tags so that tags("*") returns "@*@"
@pytest.fixture(autouse=True)
def patch_canonical_tags(monkeypatch):
    from datashuttle.configs import canonical_tags

    monkeypatch.setattr(canonical_tags, "tags", DummyCanonicalTags.tags)


# Dummy implementation for search_sub_or_ses_level that simply performs globbing.
def dummy_search_sub_or_ses_level(
    cfg, base_folder: Path, local_or_central: str, *args, search_str: str
):
    pattern = os.path.join(str(base_folder), search_str)
    matches: List[str] = sorted(glob.glob(pattern))
    return (matches,)


# Patch search_sub_or_ses_level in the module where search_for_wildcards is defined.
@pytest.fixture(autouse=True)
def patch_search_sub_or_ses_level(monkeypatch):
    monkeypatch.setattr(
        "datashuttle.utils.folders.search_sub_or_ses_level",
        dummy_search_sub_or_ses_level,
    )


# Dummy implementation for get_values_from_bids_formatted_name.
def dummy_get_values_from_bids_formatted_name(name: str, key: str) -> dict:
    # Expect name format: "sub-01_date-YYYYMMDD"
    m = re.search(r"date-(\d{8})", name)
    if m:
        return {key: m.group(1)}
    return {}


# Patch get_values_from_bids_formatted_name.
@pytest.fixture(autouse=True)
def patch_get_values_from_bids(monkeypatch):
    monkeypatch.setattr(
        "datashuttle.utils.utils.get_values_from_bids_formatted_name",
        dummy_get_values_from_bids_formatted_name,
    )


# Fixture to create a temporary directory with a simulated folder structure.
@pytest.fixture
def temp_project_dir() -> Path:  # type: ignore
    temp_dir = Path(tempfile.mkdtemp())
    # Create folders with names in the format "sub-01_date-YYYYMMDD"
    folder_dates = [
        "20250305",
        "20250306",
        "20250307",
        "20250308",
        "20250309",
        "20250310",
    ]
    for date_str in folder_dates:
        folder_name = f"sub-01_date-{date_str}"
        os.mkdir(temp_dir / folder_name)
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_date_range_wildcard(temp_project_dir: Path):
    """
    When given a date-range wildcard pattern like "sub-01_20250306@DATETO@20250309",
    only folders whose embedded date falls between 20250306 and 20250309 (inclusive)
    should be returned.
    """

    class Configs:
        pass

    cfg = Configs()
    base_folder = temp_project_dir
    local_or_central = "local"
    pattern = "sub-01_20250306@DATETO@20250309"
    result = search_for_wildcards(
        cfg, base_folder, local_or_central, [pattern]
    )

    # Extract the dates from the returned folder names.
    found_dates = set()
    for folder in result:
        basename = os.path.basename(folder)
        m = re.search(r"date-(\d{8})", basename)
        if m:
            found_dates.add(m.group(1))

    expected_dates = {"20250306", "20250307", "20250308", "20250309"}
    assert found_dates == expected_dates


def test_simple_wildcard(temp_project_dir: Path):
    """
    When given a simple wildcard pattern like "sub-01_@*@",
    all folders should be returned.
    """

    class Configs:
        pass

    cfg = Configs()
    base_folder = temp_project_dir
    local_or_central = "local"
    pattern = "sub-01_@*@"
    result = search_for_wildcards(
        cfg, base_folder, local_or_central, [pattern]
    )
    # We expect six folders.
    assert len(result) == 6
