import copy
import glob
import os
import pathlib
import shutil
import subprocess
import warnings
from os.path import join

import appdirs
import yaml

from datashuttle.datashuttle import DataShuttle


def setup_project_default_configs(
    project_name,
    local_path=False,
    remote_path=False,
):
    """"""
    delete_project_if_it_exists(project_name)

    warnings.filterwarnings("ignore")

    project = DataShuttle(project_name)

    project._setup_remote_as_rclone_target("local")

    default_configs = get_test_config_arguments_dict(set_as_defaults=True)
    project.make_config_file(*default_configs.values())

    warnings.filterwarnings("default")

    project.update_config(
        "local_path", project.get_appdir_path() + "/base_dir"
    )

    if local_path:
        project.update_config("local_path", local_path)
        delete_all_dirs_in_local_path(project)

    if remote_path:
        project.update_config("remote_path_local", remote_path)
        delete_all_dirs_in_remote_path(project)

    return project


def glob_basenames(search_path, recursive=False):
    paths_ = glob.glob(search_path, recursive=recursive)
    basenames = [os.path.basename(path_) for path_ in paths_]
    return sorted(basenames)


def teardown_project(
    cwd, project
):  # 99% sure these are unnecessary with pytest tmp_path but keep until SSH testing.
    """"""
    os.chdir(cwd)
    delete_all_dirs_in_remote_path(project)
    delete_project_if_it_exists(project.project_name)


def delete_all_dirs_in_local_path(project):
    if os.path.isdir(project.get_local_path()):
        shutil.rmtree(project.get_local_path())


def delete_all_dirs_in_remote_path(project):
    """"""
    if os.path.isdir(project.get_remote_path()):
        shutil.rmtree(project.get_remote_path())


def delete_project_if_it_exists(project_name):
    """"""
    if os.path.isdir(
        os.path.join(appdirs.user_data_dir("DataShuttle"), project_name)
    ):
        shutil.rmtree(
            os.path.join(
                appdirs.user_data_dir("DataShuttle"),
                project_name,
            )
        )


def get_test_config_arguments_dict(
    set_as_defaults=None, required_arguments_only=None
):
    """
    Retrieve configs, either the required configs
    (for project.make_config_file()), all configs (default)
    or non-default configs. Note that default configs here
    are the expected default arguments in project.make_config_file().
    """
    dict_ = {
        "local_path": r"Not:/a/real/local/directory",
        "ssh_to_remote": False,
        "remote_path_local": r"/Not/a/real/remote_local/directory",
        "remote_path_ssh": r"/not/a/real/remote_ssh/directory",
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
    Automated test that directories are made based
    on the  structure specified on project itself.

    Cycle through all experiment type (defined in
    project._ses_dirs()), sub, sessions and check that
    the expected file exists. For  subdirs, recursively
    check all exist.

    Directories in which directory_used[key] (where key
    is the cannoincal dict key in project._ses_dirs())
    is not used are expected  not to be made, and this
     is checked.

    The directory_used variable must be passed so we dont
    rely on project settings itself,
    as this doesn't explicitly test this.
    """
    for key, directory in project._ses_dirs.items():

        assert key in directory_used.keys(), (
            "Key not found in directory_used. "
            "Update directory used and hard-coded tests: "
            "test_custom_directory_names(), test_explicitly_session_list()"
        )

        if check_directory_is_used(base_dir, directory, directory_used, key):
            check_and_cd_dir(join(base_dir, directory.name))

            for sub in subs:

                check_and_cd_dir(join(base_dir, directory.name, sub))

                for ses in sessions:
                    path_to_folder = join(base_dir, directory.name, sub, ses)
                    check_and_cd_dir(path_to_folder)

                    check_and_cd_dir(path_to_folder + "/.datashuttle_meta")

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


def get_default_directory_used():
    return {
        "ephys": True,
        "ephys_behav": True,
        "ephys_behav_camera": True,
        "behav": True,
        "behav_camera": True,
        "imaging": True,
        "histology": True,
    }


def get_protected_test_dir():
    return "ds_protected_test_name"  # TODO: get from configs


def run_cli(command, project_name=None):

    name = get_protected_test_dir() if project_name is None else project_name

    result = subprocess.Popen(
        " ".join(["python -m datashuttle", name, command]),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )  # shell=True  TODO: https://stackoverflow.com/questions/2408650/why-does-python-subprocess-hang-after-proc-communicate see no use shell...

    stdout, stderr = result.communicate()
    return stdout.decode("utf8"), stderr.decode("utf8")


def setup_project_fixture(tmp_path, test_project_name):

    project = setup_project_default_configs(
        test_project_name,
        local_path=tmp_path / test_project_name / "local",
        remote_path=tmp_path / test_project_name / "remote",
    )

    cwd = os.getcwd()
    return project, cwd


def check_configs(project, kwargs):
    """"""
    config_path = (
        project.get_appdir_path() + "/config.yaml"
    )  # TODO: can use new get_config()

    if not os.path.isfile(config_path):
        raise BaseException("Config file not found.")

    check_project_configs(project, kwargs)
    check_config_file(config_path, kwargs)


def check_project_configs(
    project,
    *kwargs,
):
    """
    Core function for checking the config against
    provided configs (kwargs). Open the config.yaml file
    and check the config values stored there,
    and in project.cfg, against the provided configs.

    Paths are stored as pathlib in the cfg but str in the .yaml
    """
    for arg_name, value in kwargs[0].items():

        if arg_name in [
            "local_path",
            "remote_path_ssh",
            "remote_path_local",
        ]:
            assert type(project.cfg[arg_name]) in [
                pathlib.PosixPath,
                pathlib.WindowsPath,
            ]
            assert value == project.cfg[arg_name].as_posix()

        else:
            assert value == project.cfg[arg_name], f"{arg_name}"


def check_config_file(config_path, *kwargs):
    """ """
    with open(config_path, "r") as config_file:
        config_yaml = yaml.full_load(config_file)

        for name, value in kwargs[0].items():
            assert value == config_yaml[name], f"{name}"


def get_not_set_config_args(project):
    return {
        "local_path": r"C:/test/test_local/test_edit",
        "remote_path_local": r"/nfs/testdir/test_edit2",
        "remote_path_ssh": r"/nfs/testdir/test_edit3",
        "remote_host_id": "test_id",
        "remote_host_username": "test_host",
        "sub_prefix": "sub-optional",
        "ses_prefix": "ses-optional",
        "use_ephys": not project.cfg["use_ephys"],
        "use_ephys_behav": not project.cfg["use_ephys_behav"],
        "use_ephys_behav_camera": not project.cfg["use_ephys_behav_camera"],
        "use_behav": not project.cfg["use_behav"],
        "use_behav_camera": not project.cfg["use_behav_camera"],
        "use_histology": not project.cfg["use_histology"],
        "use_imaging": not project.cfg["use_imaging"],
        "ssh_to_remote": not project.cfg["ssh_to_remote"],
        # ^test last so ssh items already set
    }


def get_config_path_with_cli(project_name=None):
    stdout = run_cli(" get_config_path", project_name)
    path_ = stdout[0].split(".yaml")[0] + ".yaml"
    return path_


def make_and_check_local_project(project, experiment_type, subs, sessions):
    """
    Make a local project directory tree with the specified experiment_type,
    subs, sessions and check it is made successfully.
    """
    project.make_sub_dir(
        experiment_type,
        subs,
        sessions,
        get_default_directory_used(),
    )

    check_directory_tree_is_correct(
        project,
        project.get_local_path(),
        subs,
        sessions,
        get_default_directory_used(),
    )


def get_default_sub_sessions_to_test():
    """
    Cannonial subs / sessions for these tests
    """
    subs = ["sub-001", "sub-002", "sub-003"]
    sessions = ["ses-001-23092022-13h50s", "ses-002", "ses-003"]
    return subs, sessions


def check_experiment_type_sub_ses_uploaded_correctly(
    base_path_to_check,
    experiment_type_to_transfer,
    subs_to_upload=None,
    ses_to_upload=None,
):
    """
    Itereate through the project (experiment_type > ses > sub) and
    check that the directories at each level match those that are
    expected (passed in experiment / sub / ses to upload). Dirs
    are searched with wildcard glob.
    """
    experiment_names = glob_basenames(join(base_path_to_check, "*"))
    assert experiment_names == sorted(experiment_type_to_transfer)

    if subs_to_upload:
        for experiment_type in experiment_type_to_transfer:
            sub_names = glob_basenames(
                join(base_path_to_check, experiment_type, "*")
            )
            assert sub_names == sorted(subs_to_upload)

            if ses_to_upload:

                for sub in subs_to_upload:
                    ses_names = glob_basenames(
                        join(
                            base_path_to_check,
                            experiment_type,
                            sub,
                            "*",
                        )
                    )
                    assert ses_names == sorted(ses_to_upload)  #


# ----------------------------------------------------------------------------------------------------------
# Test Helpers
# ----------------------------------------------------------------------------------------------------------


def handle_upload_or_download(project, upload_or_download):
    """
    To keep things consistent and avoid the pain of writing
    files over SSH, to test download just swap the remote
    and local server (so things are still transferred from
    local machine to remote, but using the download function).
    """
    local_path = copy.deepcopy(project.get_local_path())
    remote_path = copy.deepcopy(project.get_remote_path())

    if upload_or_download == "download":

        project.update_config("local_path", remote_path)
        project.update_config("remote_path_local", local_path)

        transfer_function = project.download_data

    else:
        transfer_function = project.upload_data

    return transfer_function, remote_path
