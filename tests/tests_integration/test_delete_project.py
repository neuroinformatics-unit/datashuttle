import shutil
from datetime import datetime, timedelta

import pytest
import yaml

from datashuttle import (
    DataShuttle,
    delete_expired_trash,
    delete_project_from_disk,
    empty_trash,
    get_deleted_projects,
    restore_project_from_trash,
)
from datashuttle.configs import canonical_folders
from datashuttle.utils.custom_exceptions import (
    ConfigError,
    NeuroBlueprintError,
)

from .. import test_utils
from ..base import BaseTest


class TestDeleteProject(BaseTest):
    @pytest.fixture(autouse=True)
    def clean_trash_fixture(self):
        """Ensure trash is empty before and after tests."""
        empty_trash()
        yield
        empty_trash()

    def test_soft_delete_moves_to_trash_with_metadata(self, project):
        """Test soft delete moves project config into .trash with metadata."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        assert config_path.is_dir()
        assert project_name in [
            p.stem for p in DataShuttle.get_existing_projects()
        ]

        # Soft delete with 15 days retention
        delete_project_from_disk(
            project_name, soft_delete=True, retention_days=15
        )

        assert not config_path.exists()
        assert project_name not in [
            p.stem for p in DataShuttle.get_existing_projects()
        ]

        # Verify trash folder and metadata
        deleted = get_deleted_projects()
        assert len(deleted) >= 1
        matched = [d for d in deleted if d["project_name"] == project_name]
        assert len(matched) == 1
        assert matched[0]["retention_days"] == 15
        assert matched[0]["path"].is_dir()
        assert (matched[0]["path"] / "config.yaml").is_file()

        meta_file = matched[0]["path"] / ".deletion_metadata.yaml"
        assert meta_file.is_file()
        with open(meta_file, "r") as f:
            meta = yaml.safe_load(f)
        assert meta["original_project_name"] == project_name
        assert meta["retention_days"] == 15

    def test_restore_project_from_trash(self, project):
        """Test restoring a project from trash restores it to active projects."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        project.delete_project(soft_delete=True, retention_days=30)
        assert not config_path.exists()

        restore_project_from_trash(project_name)

        assert config_path.is_dir()
        assert (config_path / "config.yaml").is_file()
        assert not (config_path / ".deletion_metadata.yaml").exists()
        assert project_name in [
            p.stem for p in DataShuttle.get_existing_projects()
        ]

        # Re-instantiate DataShuttle on restored project to verify it loads cleanly
        reloaded = DataShuttle(project_name, print_startup_message=False)
        assert reloaded.project_name == project_name
        assert reloaded.cfg is not None

    def test_restore_project_collision_error(self, project, tmp_path):
        """Test restore raises ConfigError if an active project with same name exists."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        project.delete_project(soft_delete=True)
        assert not config_path.exists()

        # Create a new active project with the same name
        DataShuttle(project_name, print_startup_message=False)
        assert config_path.is_dir()

        with pytest.raises(ConfigError) as exc_info:
            restore_project_from_trash(project_name)
        assert "An active project with that name already exists" in str(
            exc_info.value
        )

    def test_delete_expired_trash(self, project):
        """Test delete_expired_trash only deletes projects past their expiration."""
        project_name = project.project_name

        # Delete project into trash
        delete_project_from_disk(project_name, soft_delete=True)

        deleted = get_deleted_projects()
        matched = [d for d in deleted if d["project_name"] == project_name]
        assert len(matched) == 1
        trash_path = matched[0]["path"]

        # Modify metadata to simulate an expired project (expired yesterday)
        meta_file = trash_path / ".deletion_metadata.yaml"
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        with open(meta_file, "r") as f:
            meta = yaml.safe_load(f)
        meta["expires_at"] = yesterday
        with open(meta_file, "w") as f:
            yaml.dump(meta, f)

        deleted_list = delete_expired_trash()
        assert project_name in deleted_list
        assert not trash_path.exists()

    def test_empty_trash(self, project):
        """Test empty_trash permanently deletes all items in trash."""
        project_name = project.project_name
        delete_project_from_disk(project_name, soft_delete=True)

        assert len(get_deleted_projects()) >= 1

        empty_trash()

        assert len(get_deleted_projects()) == 0

    def test_permanent_delete_bypasses_trash(self, project):
        """Test permanent delete (soft_delete=False) does not create trash entries."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        delete_project_from_disk(project_name, soft_delete=False)

        assert not config_path.exists()
        matched = [
            d
            for d in get_deleted_projects()
            if d["project_name"] == project_name
        ]
        assert len(matched) == 0

    def test_delete_project_from_disk_success(self, project):
        """Test deleting a project configuration directly using delete_project_from_disk."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        assert config_path.is_dir()
        assert (config_path / "config.yaml").is_file()
        assert project_name in [
            p.stem for p in DataShuttle.get_existing_projects()
        ]

        delete_project_from_disk(project_name)

        assert not config_path.exists()
        assert project_name not in [
            p.stem for p in DataShuttle.get_existing_projects()
        ]

    def test_delete_project_static_method(self, project):
        """Test DataShuttle.delete_project_from_disk static method."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        assert config_path.is_dir()

        DataShuttle.delete_project_from_disk(project_name)

        assert not config_path.exists()
        assert project_name not in [
            p.stem for p in DataShuttle.get_existing_projects()
        ]

    def test_delete_project_confirm_name_success(self, project):
        """Test delete_project with exact matching confirm_project_name succeeds."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        project.delete_project(
            soft_delete=False, confirm_project_name=project_name
        )
        assert not config_path.exists()

    def test_delete_project_confirm_name_mismatch_raises_error(self, project):
        """Test delete_project with mismatched confirm_project_name raises NeuroBlueprintError."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        with pytest.raises(NeuroBlueprintError) as exc_info:
            project.delete_project(
                soft_delete=False, confirm_project_name="wrong_project_name"
            )

        assert "Project name confirmation failed" in str(exc_info.value)
        assert config_path.is_dir()

    def test_delete_project_instance_method_preserve_data(
        self, project, tmp_path
    ):
        """Test project.delete_project(delete_local_data=False) removes config but preserves data."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        local_path = project.cfg["local_path"]
        assert local_path.is_dir()

        # Create dummy file in local project
        dummy_file = local_path / "rawdata" / "sub-001" / "test.txt"
        dummy_file.parent.mkdir(parents=True, exist_ok=True)
        dummy_file.write_text("important data")

        project.delete_project(delete_local_data=False)

        assert not config_path.exists()
        assert project.cfg is None
        assert dummy_file.is_file()
        assert dummy_file.read_text() == "important data"

        # Cleanup test data
        if local_path.is_dir():
            shutil.rmtree(local_path)

    def test_delete_project_instance_method_delete_local_data(
        self, project, tmp_path
    ):
        """Test project.delete_project(delete_local_data=True) deletes local data folder."""
        project_name = project.project_name
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            project_name
        )

        local_path = project.cfg["local_path"]
        assert local_path.is_dir()

        project.delete_project(delete_local_data=True)

        assert not config_path.exists()
        assert not local_path.exists()
        assert project.cfg is None

    def test_delete_project_instance_method_delete_central_data(
        self, tmp_path, clean_project_name
    ):
        """Test project.delete_project(delete_central_data=True) deletes central path for local_filesystem."""
        project = test_utils.setup_project_default_configs(
            clean_project_name,
            tmp_path,
            local_path=tmp_path / "local" / clean_project_name,
            central_path=tmp_path / "central" / clean_project_name,
        )

        local_path = project.cfg["local_path"]
        central_path = project.cfg["central_path"]
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            clean_project_name
        )

        assert local_path.is_dir()
        assert central_path.is_dir()
        assert config_path.is_dir()

        project.delete_project(
            delete_local_data=True, delete_central_data=True
        )

        assert not config_path.exists()
        assert not local_path.exists()
        assert not central_path.exists()

    def test_delete_non_existent_project(self):
        """Test that attempting to delete a non-existent project raises FileNotFoundError."""
        non_existent_name = "definitely_non_existent_project_9999"
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            non_existent_name
        )
        assert not config_path.exists()

        with pytest.raises(FileNotFoundError) as exc_info:
            delete_project_from_disk(non_existent_name)

        assert f"Cannot delete project '{non_existent_name}'" in str(
            exc_info.value
        )

    def test_delete_project_invalid_name(self):
        """Test that invalid project names raise NeuroBlueprintError."""
        for invalid_name in ["", "   "]:
            with pytest.raises(NeuroBlueprintError) as exc_info:
                delete_project_from_disk(invalid_name)
            assert "The project name must be a non-empty string" in str(
                exc_info.value
            )

    def test_delete_unconfigured_project(self, clean_project_name):
        """Test deleting a project instance that was created without make_config_file."""
        project = DataShuttle(clean_project_name, print_startup_message=False)
        config_path, _ = canonical_folders.get_project_datashuttle_path(
            clean_project_name
        )

        assert config_path.is_dir()
        assert project.cfg is None

        project.delete_project()

        assert not config_path.exists()

    def test_delete_project_cleans_up_rclone_configs(self, tmp_path):
        """Test that deleting a project removes any orphaned central_<project_name>_*.conf files."""
        project_name = "test_rclone_cleanup_proj"
        test_utils.delete_project_if_it_exists(project_name)

        rclone_base = canonical_folders.get_rclone_config_base_path()
        rclone_base.mkdir(parents=True, exist_ok=True)

        fake_rclone_conf = rclone_base / f"central_{project_name}_ssh.conf"
        fake_rclone_conf.write_text("fake rclone conf")

        project = DataShuttle(project_name, print_startup_message=False)

        assert fake_rclone_conf.is_file()

        project.delete_project(soft_delete=False)

        assert not fake_rclone_conf.exists()

    def test_delete_project_isolation(self, tmp_path):
        """Test deleting one project does not affect other existing projects."""
        proj_a_name = "test_isolation_proj_a"
        proj_b_name = "test_isolation_proj_b"

        test_utils.delete_project_if_it_exists(proj_a_name)
        test_utils.delete_project_if_it_exists(proj_b_name)

        proj_a = test_utils.setup_project_default_configs(
            proj_a_name, tmp_path
        )
        proj_b = test_utils.setup_project_default_configs(
            proj_b_name, tmp_path
        )

        existing_names = [p.stem for p in DataShuttle.get_existing_projects()]
        assert proj_a_name in existing_names
        assert proj_b_name in existing_names

        proj_a.delete_project()

        remaining_names = [p.stem for p in DataShuttle.get_existing_projects()]
        assert proj_a_name not in remaining_names
        assert proj_b_name in remaining_names

        # Cleanup project B
        proj_b.delete_project()
