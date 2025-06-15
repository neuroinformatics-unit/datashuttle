import glob
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List

import pytest

from datashuttle.utils.folders import search_with_tags


# Dummy implementation for canonical_tags
class DummyCanonicalTags:
    @staticmethod
    def tags(x: str) -> str:
        tags_dict = {
            "*": "@*@",
            "DATETO": "@DATETO@",
            "TIMETO": "@TIMETO@",
            "DATETIMETO": "@DATETIMETO@"
        }
        return tags_dict.get(x, x)

    @staticmethod
    def get_datetime_format(format_type: str) -> str:
        formats = {
            "datetime": "%Y%m%dT%H%M%S",
            "time": "%H%M%S",
            "date": "%Y%m%d",
        }
        if format_type not in formats:
            raise ValueError(f"Invalid format type: {format_type}")
        return formats[format_type]


# Patch canonical_tags
@pytest.fixture(autouse=True)
def patch_canonical_tags(monkeypatch):
    from datashuttle.configs import canonical_tags
    monkeypatch.setattr(canonical_tags, "tags", DummyCanonicalTags.tags)
    monkeypatch.setattr(canonical_tags, "get_datetime_format", DummyCanonicalTags.get_datetime_format)


# Dummy implementation for search_sub_or_ses_level that simply performs globbing.
def dummy_search_sub_or_ses_level(
    cfg, base_folder: Path, local_or_central: str, *args, search_str: str = "*"
):
    pattern = os.path.join(str(base_folder), search_str)
    matches: List[str] = sorted(glob.glob(pattern))
    return (matches, [])


# Patch search_sub_or_ses_level in the module where search_with_tags is defined.
@pytest.fixture(autouse=True)
def patch_search_sub_or_ses_level(monkeypatch):
    from datashuttle.utils import folders
    monkeypatch.setattr(folders, "search_sub_or_ses_level", dummy_search_sub_or_ses_level)


# Dummy implementation for get_values_from_bids_formatted_name
def dummy_get_values_from_bids_formatted_name(names: List[str], key: str, return_as_int: bool = False) -> List[str]:
    results = []
    for name in names:
        if key == "date":
            m = re.search(r"date-(\d{8})", name)
            if m:
                results.append(m.group(1))
    return results


# Patch get_values_from_bids_formatted_name
@pytest.fixture(autouse=True)
def patch_get_values_from_bids(monkeypatch):
    from datashuttle.utils import utils
    monkeypatch.setattr(utils, "get_values_from_bids_formatted_name", dummy_get_values_from_bids_formatted_name)


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
    result = search_with_tags(cfg, base_folder, local_or_central, [pattern])

    # Extract the dates from the returned folder names
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
    result = search_with_tags(cfg, base_folder, local_or_central, [pattern])
    # We expect six folders (20250305 through 20250310)
    assert len(result) == 6


def test_invalid_date_range(temp_project_dir: Path):
    """
    Test that invalid date ranges raise appropriate errors.
    """
    class Configs:
        pass

    cfg = Configs()
    base_folder = temp_project_dir
    local_or_central = "local"

    # Test end date before start date
    with pytest.raises(Exception) as exc_info:
        pattern = "sub-01_20250309@DATETO@20250306"
        search_with_tags(cfg, base_folder, local_or_central, [pattern])
    assert "before start" in str(exc_info.value)

    # Test invalid date format
    with pytest.raises(Exception) as exc_info:
        pattern = "sub-01_2025030@DATETO@20250306"  # Missing digit
        search_with_tags(cfg, base_folder, local_or_central, [pattern])
    assert "Invalid" in str(exc_info.value)


def test_combined_wildcards(temp_project_dir: Path):
    """
    Test that wildcard and date range can be combined in the same pattern.
    """
    class Configs:
        pass

    cfg = Configs()
    base_folder = temp_project_dir
    local_or_central = "local"

    # Create some additional test folders with different subject numbers
    for sub in ["02", "03"]:
        for date in ["20250307", "20250308"]:
            folder_name = f"sub-{sub}_date-{date}"
            os.mkdir(temp_project_dir / folder_name)

    pattern = "sub-*_20250307@DATETO@20250308"
    result = search_with_tags(cfg, base_folder, local_or_central, [pattern])

    # Should match all subjects but only dates within range
    matched_folders = set(os.path.basename(f) for f in result)
    expected_folders = {
        "sub-01_date-20250307",
        "sub-01_date-20250308",
        "sub-02_date-20250307",
        "sub-02_date-20250308",
        "sub-03_date-20250307",
        "sub-03_date-20250308",
    }
    assert matched_folders == expected_folders

