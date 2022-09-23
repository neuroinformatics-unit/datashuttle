import os
import shutil
import warnings

import appdirs

from manager.manager import ProjectManager


def setup_project_default_configs(project_name):
    """"""
    warnings.filterwarnings("ignore")

    project = ProjectManager(project_name)

    default_configs = get_test_config_arguments_dict(set_as_defaults=True)
    project.make_config_file(*default_configs.values())

    warnings.filterwarnings("default")

    project.update_config(
        "local_path", project.get_appdir_path() + "/base_dir"
    )

    return project


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
        "local_path": r"C:/test/test_local/path",
        "remote_path": r"/nfs/testdir/user",
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
