import copy
import glob
import os
import pathlib
import shutil
import subprocess
import warnings
from os.path import join
from pathlib import Path

import yaml

from datashuttle.configs import canonical_configs
from datashuttle.datashuttle import DataShuttle
from datashuttle.utils import ds_logger, rclone, utils

# -----------------------------------------------------------------------------
# Setup and Teardown Test Project
# -----------------------------------------------------------------------------


def setup_project_default_configs(
    project_name,
    tmp_path,
    local_path=False,
    remote_path=False,
    all_data_type_on=True,
):
    """
    Set up a fresh project to test on

    local_path / remote_path: provide the config paths to set
    all_data_type_on: by default, all data_type flags are False.
                     for testing, it is preferable to have all True
                     so set this if this argument is True.
    """
    delete_project_if_it_exists(project_name)

    warnings.filterwarnings("ignore")

    project = DataShuttle(project_name)

    default_configs = get_test_config_arguments_dict(
        tmp_path, set_as_defaults=True
    )

    if all_data_type_on:
        default_configs.update(get_all_data_types_on("kwargs"))

    project.make_config_file(**default_configs)

    rclone.setup_remote_as_rclone_target(
        "ssh",
        project.cfg,
        project.cfg.get_rclone_config_name("ssh"),
        project.cfg.ssh_key_path,
    )

    warnings.filterwarnings("default")

    project.update_config("local_path", project._datashuttle_path / "base_folder")

    if local_path:
        project.update_config("local_path", local_path)
        delete_all_dirs_in_local_path(project)
        project.cfg.make_and_get_logging_path()

    if remote_path:
        project.update_config("remote_path", remote_path)
        delete_all_dirs_in_project_path(project, "remote")
        project.cfg.make_and_get_logging_path()

    return project


def glob_basenames(search_path, recursive=False, exclude=None):
    """
    Use glob to search but strip the full path, including
    only the base name (lowest level).
    """
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
    delete_all_dirs_in_project_path(project, "remote")
    delete_all_dirs_in_project_path(project, "local")
    delete_project_if_it_exists(project.project_name)


def delete_all_dirs_in_local_path(project):
    ds_logger.close_log_filehandler()
    if project.cfg["local_path"].is_dir():
        shutil.rmtree(project.cfg["local_path"])


def delete_all_dirs_in_project_path(project, local_or_remote):
    """"""
    folder = f"{local_or_remote}_path"

    ds_logger.close_log_filehandler()
    if project.cfg[folder].is_dir() and project.cfg[folder].stem in [
        "local",
        "remote",
    ]:
        shutil.rmtree(project.cfg[folder])


def delete_project_if_it_exists(project_name):
    """"""
    config_path, __ = utils.get_datashuttle_path(project_name)

    if config_path.is_dir():
        ds_logger.close_log_filehandler()

    shutil.rmtree(config_path)


def make_correct_supply_config_file(
    setup_project, tmp_path, update_configs=False
):
    """"""
    new_configs_path = setup_project._datashuttle_path / "new_configs.yaml"
    new_configs = get_test_config_arguments_dict(tmp_path)

    canonical_config_dict = canonical_configs.get_canonical_config_dict()
    new_configs = {key: new_configs[key] for key in canonical_config_dict}

    if update_configs:
        new_configs[update_configs["key"]] = update_configs["value"]

    dump_config(new_configs, new_configs_path)

    return new_configs_path.as_posix(), new_configs


def dump_config(dict_, path_):
    with open(path_, "w") as config_file:
        yaml.dump(dict_, config_file, sort_keys=False)


def setup_project_fixture(tmp_path, test_project_name):
    """"""
    project = setup_project_default_configs(
        test_project_name,
        tmp_path,
        local_path=make_test_path(tmp_path, test_project_name, "local"),
        remote_path=make_test_path(tmp_path, test_project_name, "remote"),
    )

    cwd = os.getcwd()
    return project, cwd


def make_test_path(base_path, test_project_name, local_or_remote):
    return Path(base_path) / test_project_name / local_or_remote


def get_protected_test_dir():
    return "ds_protected_test_name"


# -----------------------------------------------------------------------------
# Test Configs
# -----------------------------------------------------------------------------


def get_test_config_arguments_dict(
    tmp_path,
    set_as_defaults=False,
    required_arguments_only=False,
):
    """
    Retrieve configs, either the required configs
    (for project.make_config_file()), all configs (default)
    or non-default configs. Note that default configs here
    are the expected default arguments in project.make_config_file().

    Include spaces in path so this case is always checked
    """
    tmp_path = Path(tmp_path).as_posix()

    dict_ = {
        "local_path": f"{tmp_path}/not/a/re al/local/folder",
        "remote_path": f"{tmp_path}/a/re al/remote_ local/folder",
        "connection_method": "local_filesystem",
        "use_behav": True,  # This is not explicitly required,
        # but at least 1 use_x must be true, so
        # for tests always set use_behav=True
    }

    if required_arguments_only:
        return dict_

    if set_as_defaults:
        dict_.update(
            {
                "remote_host_id": None,
                "remote_host_username": None,
                "overwrite_old_files": False,
                "transfer_verbosity": "v",
                "show_transfer_progress": False,
                "use_ephys": False,
                "use_histology": False,
                "use_funcimg": False,
            }
        )
    else:
        dict_.update(
            {
                "local_path": f"{tmp_path}/test/test_ local/test_edit",
                "remote_path": f"{tmp_path}/nfs/test folder/test_edit2",
                "connection_method": "ssh",
                "remote_host_id": "test_remote_host_id",
                "remote_host_username": "test_remote_host_username",
                "overwrite_old_files": True,
                "transfer_verbosity": "vv",
                "show_transfer_progress": True,
                "use_ephys": True,
                "use_behav": False,
                "use_histology": True,
                "use_funcimg": True,
            }
        )

    return dict_


def get_default_folder_used():
    return {
        "ephys": True,
        "behav": True,
        "funcimg": True,
        "histology": True,
    }


def get_config_path_with_cli(project_name=None):
    stdout = run_cli(" get_config_path", project_name)
    path_ = stdout[0].split(".yaml")[0] + ".yaml"
    return path_


def add_quotes(string: str):
    return '"' + string + '"'


# -----------------------------------------------------------------------------
# Folder Checkers
# -----------------------------------------------------------------------------


def check_folder_tree_is_correct(
    project, base_folder, subs, sessions, folder_used
):
    """
    Automated test that folders are made based
    on the structure specified on project itself.

    Cycle through all data_types (defined in
    project.cfg.data_type_folders()), sub, sessions and check that
    the expected file exists. For  subdirs, recursively
    check all exist.

    Folders in which folder_used[key] (where key
    is the canonical dict key in project.cfg.data_type_folders())
    is not used are expected  not to be made, and this
     is checked.

    The folder_used variable must be passed so we don't
    rely on project settings itself,
    as this doesn't explicitly test this.
    """
    for sub in subs:

        path_to_sub_folder = join(base_folder, sub)
        check_and_cd_dir(path_to_sub_folder)

        for ses in sessions:

            path_to_ses_folder = join(base_folder, sub, ses)
            check_and_cd_dir(path_to_ses_folder)

            for key, folder in project.cfg.data_type_folders.items():

                assert key in folder_used.keys(), (
                    "Key not found in folder_used. "
                    "Update folder used and hard-coded tests: "
                    "test_custom_folder_names(), test_explicitly_session_list()"
                )

                if check_folder_is_used(
                    base_folder, folder, folder_used, key, sub, ses
                ):

                    if folder.level == "sub":
                        data_type_path = join(
                            path_to_sub_folder, folder.name
                        )
                    elif folder.level == "ses":
                        data_type_path = join(
                            path_to_ses_folder, folder.name
                        )

                    check_and_cd_dir(data_type_path)
                    check_and_cd_dir(join(data_type_path, ".datashuttle_meta"))


def check_folder_is_used(
    base_folder, folder, folder_used, key, sub, ses
):
    """
    Test whether the .used flag on the Folder class matched the expected
    state (provided in folder_used dict). If folder is not used, check
    it does not exist.

    Use the pytest -s flag to print all tested paths
    """
    assert folder.used == folder_used[key]

    is_used = folder.used

    if not is_used:
        print(
            "Path was correctly not made: "
            + join(base_folder, sub, ses, folder.name)
        )
        assert not os.path.isdir(join(base_folder, sub, ses, folder.name))

    return is_used


def check_and_cd_dir(path_):
    """
    Check a folder exists and CD to it if it does.

    Use the pytest -s flag to print all tested paths
    """
    assert os.path.isdir(path_)
    os.chdir(path_)


def check_data_type_sub_ses_uploaded_correctly(
    base_path_to_check,
    data_type_to_transfer,
    subs_to_upload=None,
    ses_to_upload=None,
):
    """
    Iterate through the project (data_type > ses > sub) and
    check that the folders at each level match those that are
    expected (passed in data_type / sub / ses to upload). Dirs
    are searched with wildcard glob.

    Note: might be easier to flatten entire path with glob(**)
    then search...
    """
    if subs_to_upload:
        sub_names = glob_basenames(join(base_path_to_check, "*"))
        assert sub_names == sorted(subs_to_upload)

        # Check ses are all uploaded + histology if transferred
        if ses_to_upload:

            for sub in subs_to_upload:
                ses_names = glob_basenames(
                    join(
                        base_path_to_check,
                        sub,
                        "*",
                    )
                )
                if data_type_to_transfer == ["histology"]:
                    assert ses_names == ["histology"]
                    return  # handle the case in which histology
                    # only is transferred,
                    # and there are no sessions to transfer.

                copy_data_type_to_transfer = (
                    check_and_strip_within_sub_data_dirs(
                        ses_names, data_type_to_transfer
                    )
                )
                assert ses_names == sorted(ses_to_upload)

                # check data_type folders in session folder
                if copy_data_type_to_transfer:
                    for ses in ses_names:
                        data_names = glob_basenames(
                            join(base_path_to_check, sub, ses, "*")
                        )
                        assert data_names == sorted(copy_data_type_to_transfer)


def check_and_strip_within_sub_data_dirs(ses_names, data_type_to_transfer):
    """
    Check if data_type folders at the sub level are picked
    up when sessions are searched for with wildcard. Remove
    so that sessions can be explicitly tested next.
    """
    if "histology" in data_type_to_transfer:
        assert "histology" in ses_names

        ses_names.remove("histology")
        copy_ = copy.deepcopy(data_type_to_transfer)
        copy_.remove("histology")
        return copy_
    return data_type_to_transfer


def make_and_check_local_project(project, subs, sessions, data_type):
    """
    Make a local project folder tree with the specified data_type,
    subs, sessions and check it is made successfully.
    """
    project.make_sub_folders(subs, sessions, data_type)

    check_folder_tree_is_correct(
        project,
        get_rawdata_path(project),
        subs,
        sessions,
        get_default_folder_used(),
    )


# -----------------------------------------------------------------------------
# Config Checkers
# -----------------------------------------------------------------------------


def check_configs(project, kwargs):
    """"""
    config_path = project._config_path

    if not config_path.is_file():
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

        if arg_name in project.cfg.keys_str_on_file_but_path_in_class:
            assert type(project.cfg[arg_name]) in [
                pathlib.PosixPath,
                pathlib.WindowsPath,
            ]
            assert value == project.cfg[arg_name].as_posix()

        else:
            assert value == project.cfg[arg_name], f"{arg_name}"


def check_config_file(config_path, *kwargs):
    """"""
    with open(config_path, "r") as config_file:
        config_yaml = yaml.full_load(config_file)

        for name, value in kwargs[0].items():
            assert value == config_yaml[name], f"{name}"


# -----------------------------------------------------------------------------
# Test Helpers
# -----------------------------------------------------------------------------


def get_rawdata_path(project, local_or_remote="local"):
    """"""
    if local_or_remote == "local":
        base_path = project.cfg["local_path"]
    else:
        base_path = project.cfg["remote_path"]
    return os.path.join(base_path, project.cfg.top_level_folder_name)


def handle_upload_or_download(
    project,
    upload_or_download,
    use_all_alias=False,
    swap_last_dir_only=False,
):
    """
    To keep things consistent and avoid the pain of writing
    files over SSH, to test download just swap the remote
    and local server (so things are still transferred from
    local machine to remote, but using the download function).
    """
    if upload_or_download == "download":

        remote_path = swap_local_and_remote_paths(project, swap_last_dir_only)

        transfer_function = (
            project.download_all if use_all_alias else project.download_data
        )

    else:
        remote_path = project.cfg["remote_path"]

        transfer_function = (
            project.upload_all if use_all_alias else project.upload_data
        )

    return transfer_function, remote_path


def swap_local_and_remote_paths(project, swap_last_dir_only=False):
    """
    When testing upload vs. download, the most convenient way
    to test download is to swap the paths. In this case, we 'download'
    from local to remote. It much simplifies creating the folders
    to transfer (which are created locally), and is fully required
    in tests with session scope fixture, in which a local project
    is made only once and repeatedly transferred.

    Typically, this is as simple as swapping remote and local.
    For SSH test however, we want to use SSH to search the 'remote'
    filesystem to find the necsesary files / folders to transfer.
    As such, the 'local' (which we are downloading from) must be the SSH
    path. As such, in this case we only want to swap the last dir only
    (i.e. "local" and "remote"). In this case, we download from
    cfg["remote_path"] (which is ssh_path/local) to cfg["local_path"]
    (which is filesystem/remote).
    """
    local_path = copy.deepcopy(project.cfg["local_path"])
    remote_path = copy.deepcopy(project.cfg["remote_path"])

    if swap_last_dir_only:
        project.update_config(
            "local_path", local_path.parent / remote_path.name
        )
        project.update_config(
            "remote_path", remote_path.parent / local_path.name
        )
    else:
        project.update_config("local_path", remote_path)
        project.update_config("remote_path", local_path)

    return remote_path


def get_default_sub_sessions_to_test():
    """
    Canonical subs / sessions for these tests
    """
    subs = ["sub-001", "sub-002", "sub-003"]
    sessions = ["ses-001_23092022-13h50s", "ses-002", "ses-003"]
    return subs, sessions


def run_cli(command, project_name=None):
    """"""
    name = get_protected_test_dir() if project_name is None else project_name

    result = subprocess.Popen(
        " ".join(["datashuttle", name, command]),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    stdout, stderr = result.communicate()
    return stdout.decode("utf8"), stderr.decode("utf8")


def get_all_data_types_on(kwargs_or_flags):
    """
    Get all data_types (e.g. --use_behav) in on form,
    either as kwargs for API or str of flags for
    CLI.
    """
    data_types = canonical_configs.get_data_types()
    if kwargs_or_flags == "flags":
        return f"{' '.join(['--' + flag for flag in data_types])}"
    else:
        return dict(zip(data_types, [True] * len(data_types)))


def move_some_keys_to_end_of_dict(config):
    """
    Need to move connection method to the end
    so ssh opts are already set before it is changed. Similarly,
    use_behav must be turned off after at least one other use_
    option is turned on.
    """
    config["connection_method"] = config.pop("connection_method")
    config["use_behav"] = config.pop("use_behav")


def clear_capsys(capsys):
    """
    read from capsys clears it, so new
    print statements are clearer to read.
    """
    capsys.readouterr()


def write_file(path_, contents="", append=False):
    key = "a" if append else "w"
    with open(path_, key) as file:
        file.write(contents)


def read_file(path_):
    with open(path_, "r") as file:
        contents = file.readlines()
    return contents
