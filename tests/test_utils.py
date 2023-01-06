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

# ----------------------------------------------------------------------------------------------------------
# Setup and Teardown Test Project
# ----------------------------------------------------------------------------------------------------------


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
    project.make_config_file(**default_configs)

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


def glob_basenames(search_path, recursive=False, exclude=None):
    paths_ = glob.glob(search_path, recursive=recursive)
    basenames = [os.path.basename(path_) for path_ in paths_]

    if exclude:
        basenames = [name for name in basenames if name not in exclude]

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


def setup_project_fixture(tmp_path, test_project_name):

    project = setup_project_default_configs(
        test_project_name,
        local_path=tmp_path / test_project_name / "local",
        remote_path=tmp_path / test_project_name / "remote",
    )

    cwd = os.getcwd()
    return project, cwd


def get_protected_test_dir():
    return "ds_protected_test_name"


# ----------------------------------------------------------------------------------------------------------
# Test Configs
# ----------------------------------------------------------------------------------------------------------


def get_test_config_arguments_dict(
    set_as_defaults=None, required_arguments_only=None
):
    """
    Retrieve configs, either the required configs
    (for project.make_config_file()), all configs (default)
    or non-default configs. Note that default configs here
    are the expected default arguments in project.make_config_file().

    Include spaces in path so this case is always checked
    """
    dict_ = {
        "local_path": r"Not:/a/re al/local/directory",
        "remote_path_local": r"/Not/a/re al/remote_ local/directory",
        "remote_path_ssh": r"/not/a/re al/remote_ ssh/directory",
    }

    if required_arguments_only:
        return dict_

    if set_as_defaults:
        dict_.update(
            {
                "remote_host_id": None,
                "remote_host_username": None,
                "use_ephys": True,
                "use_behav": True,
                "use_histology": True,
                "use_imaging": True,
                "ssh_to_remote": False,
            }
        )
    else:
        dict_.update(
            {
                "remote_host_id": "test_remote_host_id",
                "remote_host_username": "test_remote_host_username",
                "use_ephys": False,
                "use_behav": False,
                "use_histology": False,
                "use_imaging": False,
                "ssh_to_remote": True,
            }
        )
    return dict_


def get_not_set_config_args(project):
    """
    Include spaces in path so this case is always checked
    """
    return {
        "local_path": r"C:/test/test_ local/test_edit",
        "remote_path_local": r"/nfs/test dir/test_edit2",
        "remote_path_ssh": r"/nfs/test dir/test_edit3",
        "remote_host_id": "test_id",
        "remote_host_username": "test_host",
        "use_ephys": not project.cfg["use_ephys"],
        "use_behav": not project.cfg["use_behav"],
        "use_histology": not project.cfg["use_histology"],
        "use_imaging": not project.cfg["use_imaging"],
        "ssh_to_remote": not project.cfg["ssh_to_remote"],
        # ^test last so ssh items already set
    }


def get_default_directory_used():
    return {
        "ephys": True,
        "behav": True,
        "imaging": True,
        "histology": True,
    }


def get_config_path_with_cli(project_name=None):
    stdout = run_cli(" get_config_path", project_name)
    path_ = stdout[0].split(".yaml")[0] + ".yaml"
    return path_


def add_quotes(string: str):
    return '"' + string + '"'


# ----------------------------------------------------------------------------------------------------------
# Directory Checkers
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
    for sub in subs:

        path_to_sub_folder = join(base_dir, sub)
        check_and_cd_dir(path_to_sub_folder)

        for ses in sessions:

            path_to_ses_folder = join(base_dir, sub, ses)
            check_and_cd_dir(path_to_ses_folder)

            for key, directory in project._ses_dirs.items():

                assert key in directory_used.keys(), (
                    "Key not found in directory_used. "
                    "Update directory used and hard-coded tests: "
                    "test_custom_directory_names(), test_explicitly_session_list()"
                )

                if check_directory_is_used(
                    base_dir, directory, directory_used, key, sub, ses
                ):

                    if directory.level == "sub":
                        experiment_type_path = join(
                            path_to_sub_folder, directory.name
                        )  # TODO: Remove directory to exp_type_path
                    elif directory.level == "ses":
                        experiment_type_path = join(
                            path_to_ses_folder, directory.name
                        )

                    check_and_cd_dir(experiment_type_path)
                    check_and_cd_dir(
                        join(experiment_type_path, ".datashuttle_meta")
                    )


def check_directory_is_used(
    base_dir, directory, directory_used, key, sub, ses
):
    """
    Test whether the .used flag on the Directory class matched the expected
    state (provided in directory_used dict). If directory is not used, check
    it does not exist.

    Use the pytest -s flag to print all tested paths
    """
    assert directory.used == directory_used[key]

    is_used = directory.used

    if not is_used:
        print(
            "Path was correctly not made: "
            + join(base_dir, sub, ses, directory.name)
        )
        assert not os.path.isdir(join(base_dir, sub, ses, directory.name))

    return is_used


def check_and_cd_dir(path_):
    """
    Check a directory exists and CD to it if it does.

    Use the pytest -s flag to print all tested paths
    """
    assert os.path.isdir(path_)
    os.chdir(path_)


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

    Note: might be easier to flatten entire path with glob(**)
    then search...
    """
    if subs_to_upload:
        sub_names = glob_basenames(join(base_path_to_check, "*"))
        assert sub_names == sorted(subs_to_upload)

        # Check ses are all upldoated + histology if transferred
        if ses_to_upload:

            for sub in subs_to_upload:
                ses_names = glob_basenames(
                    join(
                        base_path_to_check,
                        sub,
                        "*",
                    )
                )
                if experiment_type_to_transfer == ["histology"]:
                    assert ses_names == ["histology"]
                    return  # handle the case in which histolgoy only is transffered,
                    # and there are no sessions to transfer.

                copy_experiment_type_to_transfer = (
                    check_and_strip_within_sub_experiment_dirs(
                        ses_names, experiment_type_to_transfer
                    )
                )
                assert ses_names == sorted(ses_to_upload)

                # check experiment_type directories in session folder
                if copy_experiment_type_to_transfer:
                    for ses in ses_names:
                        experiment_names = glob_basenames(
                            join(base_path_to_check, sub, ses, "*")
                        )
                        assert experiment_names == sorted(
                            copy_experiment_type_to_transfer
                        )


def check_and_strip_within_sub_experiment_dirs(
    ses_names, experiment_type_to_transfer
):
    if "histology" in experiment_type_to_transfer:
        assert "histology" in ses_names

        ses_names.remove("histology")
        copy_ = copy.deepcopy(experiment_type_to_transfer)
        copy_.remove("histology")
        return copy_
    return experiment_type_to_transfer


def make_and_check_local_project(project, subs, sessions, experiment_type):
    """
    Make a local project directory tree with the specified experiment_type,
    subs, sessions and check it is made successfully.
    """
    project.make_sub_dir(subs, sessions, experiment_type)

    check_directory_tree_is_correct(
        project,
        get_rawdata_path(project),
        subs,
        sessions,
        get_default_directory_used(),
    )


# ----------------------------------------------------------------------------------------------------------
# Config Checkers
# ----------------------------------------------------------------------------------------------------------


def check_configs(project, kwargs):
    """"""
    config_path = project.get_appdir_path() + "/config.yaml"

    if not os.path.isfile(config_path):
        raise FileNotFoundError("Config file not found.")

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


# ----------------------------------------------------------------------------------------------------------
# Test Helpers
# ----------------------------------------------------------------------------------------------------------


def get_rawdata_path(project, local_or_remote="local"):
    if local_or_remote == "local":
        base_path = project.get_local_path()
    else:
        base_path = project.get_remote_path()
    return os.path.join(base_path, project._top_level_dir_name)


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


def get_default_sub_sessions_to_test():
    """
    Canonical subs / sessions for these tests
    """
    subs = ["sub-001", "sub-002", "sub-003"]
    sessions = ["ses-001-23092022-13h50s", "ses-002", "ses-003"]
    return subs, sessions


def run_cli(command, project_name=None):

    name = get_protected_test_dir() if project_name is None else project_name

    result = subprocess.Popen(
        " ".join(["datashuttle", name, command]),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    stdout, stderr = result.communicate()
    return stdout.decode("utf8"), stderr.decode("utf8")
