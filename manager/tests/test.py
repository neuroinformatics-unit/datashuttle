# TODO: setup fixtures
import sys

sys.path.append("/Users/easyelectrophysiology/git-repos/project_manager_swc")

import copy
import os
import pathlib
import shutil
import warnings

import appdirs
import yaml

from manager import ProjectManager


class TestConfigs:
    # TODO: decide on best way to use pytest fixture and use pytest

    def test_warning_on_startup(self):
        """"""
        with warnings.catch_warnings(record=True) as w:
            self.create_new_user_project()

        assert len(w) == 1
        assert (
            str(w[0].message)
            == "Configuration file has not been initialized. Use make_config_file() to setup before continuing."
        )

    def test_required_configs(self):
        """"""
        project = self.create_new_user_project()

        test_local_path, test_remote_path, test_ssh_to_remote = [
            r"C:/test\test_local/path",
            r"/nfs/testdir/user",
            False,
        ]

        project.make_config_file(
            test_local_path, test_remote_path, test_ssh_to_remote
        )

        self.check_config_reopen_and_check_config_again(
            project, test_local_path, test_remote_path, test_ssh_to_remote
        )

    def check_config_reopen_and_check_config_again(
        self, project, test_local_path, test_remote_path, test_ssh_to_remote
    ):
        """"""
        self.check_config_file(
            project, test_local_path, test_remote_path, test_ssh_to_remote
        )

        del project

        project = ProjectManager("test1")  # TODO: central loader

        self.check_config_file(
            project, test_local_path, test_remote_path, test_ssh_to_remote
        )  # TODO: tidy, (checking again on new file load).

    def check_config_file(
        self,
        project,
        local_path,
        remote_path,
        ssh_to_remote,
        remote_host_id=None,
        remote_host_username=None,
        sub_prefix="sub-",
        ses_prefix="ses-",
        use_ephys=True,
        use_ephys_behav=True,
        use_ephys_behav_camera=True,
        use_behav=True,
        use_behav_camera=True,
        use_microscopy=True,
    ):
        """ """
        function_args = copy.copy(locals())
        [function_args.pop(key) for key in ["self", "project"]]

        config_path = project.get_appdir_path() + "/config.yaml"

        if not os.path.isfile(config_path):
            raise BaseException("Config file not found.")

        with open(config_path, "r") as config_file:
            config_yaml = yaml.full_load(config_file)

        for arg_name, value in function_args.items():
            if arg_name in ["remote_path", "local_path"]:
                assert type(project.cfg[arg_name]) in [
                    pathlib.Path,
                    pathlib.PosixPath,
                ]
                assert value == str(project.cfg[arg_name])
            else:
                assert value == project.cfg[arg_name]
            assert value == config_yaml[arg_name]

    def test_optional_configs(self):
        pass

    def test_update_path_configs(self):
        pass

    def test_update_non_path_configs(self):
        pass

    def create_new_user_project(self):

        username = "test1"

        if os.path.isdir(
            os.path.join(appdirs.user_data_dir("ProjectManagerSWC"), username)
        ):  # TODO! this is not system agnostic, need to use os.path.join(appdirs.user_data_dir("ProjectManagerSWC"), username)
            shutil.rmtree(
                os.path.join(
                    appdirs.user_data_dir("ProjectManagerSWC"), username
                )
            )

        project = ProjectManager(username)

        return project


# TOOD: use pytest
test = TestConfigs()
project = ProjectManager("test1")
test.test_required_configs()
