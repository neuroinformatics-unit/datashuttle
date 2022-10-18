import glob
import os
import shutil
import warnings
from os.path import join

import appdirs

from manager.manager import ProjectManager
from manager.utils_mod import rclone_utils


def setup_project_default_configs(
    project_name,
    local_path=False,
    remote_path=False,
):
    """"""
    if not rclone_utils.check_rclone_exists():
        rclone_utils.download_rclone()

    delete_project_if_it_exists(project_name)

    warnings.filterwarnings("ignore")

    project = ProjectManager(project_name)
    project._setup_remote_as_rclone_target(
        "mounted"
    )  # TODO: check this is efficiently handled in manager

    default_configs = get_test_config_arguments_dict(set_as_defaults=True)
    project.make_config_file(*default_configs.values())

    warnings.filterwarnings("default")

    project.update_config(
        "local_path", project.get_appdir_path() + "/base_dir"
    )

    if local_path:
        project.update_config("local_path", local_path)

    if remote_path:
        project.update_config("remote_path", remote_path)
        delete_all_dirs_in_remote_path(project)

    return project


def glob_basenames(search_path, recursive=False):
    paths_ = glob.glob(search_path, recursive=recursive)
    basenames = [os.path.basename(path_) for path_ in paths_]
    return basenames


def teardown_project(cwd, project):
    """"""
    os.chdir(cwd)
    delete_all_dirs_in_remote_path(project)
    delete_project_if_it_exists(project.project_name)


def delete_all_dirs_in_remote_path(project):
    """"""
    #   if os.path.isdir(project.get_local_path()):
    #      shutil.rmtree(project.get_local_path())

    if os.path.isdir(project.get_remote_path()):
        shutil.rmtree(project.get_remote_path())


def delete_project_if_it_exists(project_name):
    """"""
    if os.path.isdir(
        os.path.join(appdirs.user_data_dir("ProjectManagerSWC"), project_name)
    ):
        shutil.rmtree(
            os.path.join(
                appdirs.user_data_dir("ProjectManagerSWC"),
                project_name,
            )
        )


def get_test_config_arguments_dict(
    set_as_defaults=None, required_arguments_only=None
):
    """
    Retrieve configs, either the required configs (for project.make_config_file()),
    all configs (default) or non-default configs. Note that default configs here
    are the expected default arguments in project.make_config_file().
    """
    dict_ = {
        "local_path": r"Not:/a/real/local/directory",
        "remote_path": r"/Not/a/real/remote/directory",
        "ssh_to_remote": False,
    }

    if required_arguments_only:
        return dict_

    if set_as_defaults:
        dict_.update(
            {
                "remote_host_id": None,
                "remote_host_username": None,
                "sub_prefix": "sub-",
                "ses_prefix": "ses-",
                "use_ephys": True,
                "use_ephys_behav": True,
                "use_ephys_behav_camera": True,
                "use_behav": True,
                "use_behav_camera": True,
                "use_histology": True,
                "use_imaging": True,
            }
        )
    else:
        dict_.update(
            {
                "ssh_to_remote": True,
                "remote_host_id": "test_remote_host_id",
                "remote_host_username": "test_remote_host_username",
                "sub_prefix": "testsub-",
                "ses_prefix": "testses-",
                "use_ephys": False,
                "use_ephys_behav": False,
                "use_ephys_behav_camera": False,
                "use_behav": False,
                "use_behav_camera": False,
                "use_histology": False,
                "use_imaging": False,
            }
        )

    return dict_


# ----------------------------------------------------------------------------------------------------------
# Test Helpers
# ----------------------------------------------------------------------------------------------------------


def check_directory_tree_is_correct(
    project, base_dir, subs, sessions, directory_used
):
    """
    Automated test that directories are made based on the structure specified on project itself.

    Cycle through all experiment type (defined in project._ses_dirs()), sub, sessions
    and check that the expected file exists. For subdirs, recursively check all exist.

    Directories in which directory_used[key] (where key is the cannoincal dict
    key in project._ses_dirs()) is not used are expected not to be made, and this is checked.

    The directory_used variable must be passed so we dont rely on project settings itself,
    as this doesn't explicitly test this.
    """
    for key, directory in project._ses_dirs.items():

        assert key in directory_used.keys(), (
            "Key not found in directory_used. "
            "Update directory used and hard-coded tests: test_custom_directory_names(), test_explicitly_session_list()"
        )

        if check_directory_is_used(base_dir, directory, directory_used, key):
            check_and_cd_dir(join(base_dir, directory.name))

            for sub in subs:
                check_and_cd_dir(join(base_dir, directory.name, sub))

                for ses in sessions:
                    path_to_folder = join(base_dir, directory.name, sub, ses)
                    check_and_cd_dir(path_to_folder)

                    recursive_check_subfolder_exists(
                        path_to_folder, directory, directory_used
                    )


def recursive_check_subfolder_exists(path_to_dir, upper_dir, directory_used):
    """
    Check each subdir in the subdirs field on the Directory class are
    made, and that directory_used is as expected.
    """
    if upper_dir.subdirs:
        for key, subdir in upper_dir.subdirs.items():

            if check_directory_is_used(
                path_to_dir, subdir, directory_used, key
            ):
                new_path_to_dir = join(path_to_dir, subdir.name)

                check_and_cd_dir(new_path_to_dir)
                recursive_check_subfolder_exists(
                    new_path_to_dir, subdir, directory_used
                )


def check_directory_is_used(base_dir, directory, directory_used, key):
    """
    Test whether the .used flag on the Directory class matched the expected
    state (provided in directory_used dict). If directory is not used, check
    it does not exist.

    Use the pytest -s flag to print all tested paths
    """
    assert directory.used == directory_used[key]

    is_used = directory.used

    if not is_used:
        print("Path was correctly not made: " + join(base_dir, directory.name))
        assert not os.path.isdir(join(base_dir, directory.name))

    return is_used


def check_and_cd_dir(path_):
    """
    Check a directory exists and CD to it if it does.

    Use the pytest -s flag to print all tested paths
    """
    assert os.path.isdir(path_)
    os.chdir(path_)
    print(f"checked: {path_}")  # -s flag


def get_default_directory_used():  # TODO: need to find a way to know to update this when new ones added
    return {
        "ephys": True,
        "ephys_behav": True,
        "ephys_behav_camera": True,
        "behav": True,
        "behav_camera": True,
        "imaging": True,
        "histology": True,
    }
