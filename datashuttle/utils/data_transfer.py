from pathlib import Path
from typing import List, Optional, Union

from datashuttle.configs.config_class import Configs

from . import folders, formatting, rclone, utils


class TransferData:
    def __init__(
        self,
        cfg: Configs,
        upload_or_download: str,
        sub_names: Union[str, List[str]],
        ses_names: Union[str, List[str]],
        data_type: Union[str, List[str]],
        dry_run: bool,
        log: bool,
    ):

        self.cfg = cfg
        self.upload_or_download = upload_or_download
        self.local_or_remote = (
            "local" if upload_or_download == "upload" else "remote"
        )
        self.base_dir = self.cfg.get_base_dir(self.local_or_remote)

        self.sub_names = self.to_list(sub_names)
        self.ses_names = self.to_list(ses_names)
        self.data_type = self.to_list(data_type)

        self.check_input_arguments()

        include_list = self.build_a_list_of_all_files_and_folders_to_transfer()

        if any(include_list):

            output = rclone.transfer_data(
                cfg,
                upload_or_download,
                include_list,
                cfg.make_rclone_transfer_options(dry_run),
            )

            if log:
                utils.log_and_message(output.stderr.decode("utf-8"))
        else:
            if log:
                utils.log_and_message("No files included. None transferred.")

    # -------------------------------------------------------------------------
    # Build the --include list
    # -------------------------------------------------------------------------

    def build_a_list_of_all_files_and_folders_to_transfer(self) -> List[str]:
        """ """
        # Find sub names to transfer
        processed_sub_names = self.get_processed_names(self.sub_names)

        sub_ses_dtype_include: List[str] = []
        extra_dirnames: List[str] = []
        extra_filenames: List[str] = []

        for sub in processed_sub_names:

            # subjects at top level dir ---------------------------------------

            if sub == "all_non_sub":
                self.update_list_with_non_sub_top_level_dirs(
                    extra_dirnames, extra_filenames
                )
                continue

            self.update_list_with_dtype_paths(
                sub_ses_dtype_include,
                self.data_type,
                sub,
            )

            # sessions at sub level dir ---------------------------------------

            processed_ses_names = self.get_processed_names(self.ses_names, sub)

            for ses in processed_ses_names:

                if ses == "all_non_ses":
                    self.update_list_with_non_ses_sub_level_dirs(
                        extra_dirnames, extra_filenames, sub
                    )

                    continue

                # Datatype (sub and ses level) --------------------------------

                if self.transfer_non_data_type(self.data_type):
                    self.update_list_with_non_dtype_ses_level_dirs(
                        extra_dirnames, extra_filenames, sub, ses
                    )

                self.update_list_with_dtype_paths(
                    sub_ses_dtype_include,
                    self.data_type,
                    sub,
                    ses,
                )

        include_list = (
            self.make_include_arg(sub_ses_dtype_include)
            + self.make_include_arg(extra_dirnames)
            + self.make_include_arg(extra_filenames, recursive=False)
        )

        return include_list

    def make_include_arg(
        self, list_of_paths: List[str], recursive: bool = True
    ) -> List[str]:
        """ """
        if not any(list_of_paths):
            return []

        if recursive:
            include_arg = lambda ele: f""" --include "{ele}/**" """
        else:
            include_arg = lambda ele: f""" --include "{ele}" """

        return ["".join([include_arg(ele) for ele in list_of_paths])]

    # -------------------------------------------------------------------------
    # Search for non-sub / ses / dtype dirs and add them to list
    # -------------------------------------------------------------------------

    def update_list_with_non_sub_top_level_dirs(
        self, extra_dirnames, extra_filenames
    ):
        top_level_dirs, top_level_files = folders.search_sub_or_ses_level(
            self.cfg,
            self.cfg.get_base_dir(self.local_or_remote),
            self.local_or_remote,
            search_str="*",
        )

        top_level_dirs = list(
            filter(lambda dir: dir[:4] != "sub-", top_level_dirs)
        )

        extra_dirnames += top_level_dirs
        extra_filenames += top_level_files

    def update_list_with_non_ses_sub_level_dirs(
        self, extra_dirnames, extra_filenames, sub
    ):
        """ """
        sub_level_dirs, sub_level_files = folders.search_sub_or_ses_level(
            self.cfg,
            self.cfg.get_base_dir(self.local_or_remote),
            self.local_or_remote,
            sub=sub,
            search_str="*",
        )
        sub_level_dtype = [
            dtype.name
            for dtype in self.cfg.data_type_dirs.values()
            if dtype.level == "sub"
        ]

        filt_sub_level_dirs = filter(
            lambda dir: dir[:4] != "ses-" and dir not in sub_level_dtype,
            sub_level_dirs,
        )
        extra_dirnames += ["/".join([sub, dir]) for dir in filt_sub_level_dirs]
        extra_filenames += ["/".join([sub, file]) for file in sub_level_files]

    def update_list_with_non_dtype_ses_level_dirs(
        self, extra_dirnames, extra_filenames, sub, ses
    ):

        (
            ses_level_dirs,
            ses_level_filenames,
        ) = folders.search_sub_or_ses_level(
            self.cfg,
            self.cfg.get_base_dir(self.local_or_remote),
            self.local_or_remote,
            sub=sub,
            ses=ses,
            search_str="*",
        )

        ses_level_dtype = [
            dtype.name
            for dtype in self.cfg.data_type_dirs.values()
            if dtype.level == "ses"
        ]
        filt_ses_level_dirs = filter(
            lambda dir: dir not in ses_level_dtype, ses_level_dirs
        )
        extra_dirnames += [
            "/".join([sub, ses, dir]) for dir in filt_ses_level_dirs
        ]
        extra_filenames += [
            "/".join([sub, ses, file]) for file in ses_level_filenames
        ]

    # -------------------------------------------------------------------------
    # Update list with path to sub and ses level data_type folders
    # -------------------------------------------------------------------------

    def update_list_with_dtype_paths(
        self,
        sub_ses_dtype_include,
        data_type: List[str],
        sub: str,
        ses: Optional[str] = None,
    ) -> None:
        """ """
        data_type = list(
            filter(lambda x: x != "all_ses_level_non_data_type", data_type)
        )

        data_type_items = self.cfg.items_from_data_type_input(
            self.local_or_remote, data_type, sub, ses
        )

        level = "ses" if ses else "sub"

        for data_type_key, data_type_dir in data_type_items:  # type: ignore

            if data_type_dir.level == level:
                if ses:
                    filepath = Path(sub) / ses / data_type_dir.name
                else:
                    filepath = Path(sub) / data_type_dir.name

                sub_ses_dtype_include.append(filepath.as_posix())

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

    def to_list(self, names: Union[str, List[str]]) -> List[str]:
        if isinstance(names, str):
            names = [names]
        return names

    def check_input_arguments(
        self,
    ):
        """
        Check the sub / session names passed. The checking here
        is stricter than for make_sub_dirs / formatting.check_and_format_names
        because we want to ensure that a) non-data-type arguments are not
        passed at the wrong input (e.g. all_non_ses as a subject name).

        We also want to limit the possible combinations of inputs, such
        that is a user inputs "all" subjects,  or "all_sub", they should
        not also pass specific subs (e.g. "sub-001"). However, all_non_sub
        and sub-001 would be permitted.

        Parameters
        ----------

        see update_list_with_dtype_paths()
        """
        if len(self.sub_names) > 1 and any(
            [name in ["all", "all_sub"] for name in self.sub_names]
        ):
            utils.log_and_raise_error(
                "'sub_names' must only include 'all' or 'all_subs' if these options are used."
            )

        if len(self.ses_names) > 1 and any(
            [name in ["all", "all_ses"] for name in self.ses_names]
        ):
            utils.log_and_raise_error(
                "'ses_names' must only include 'all' or 'all_ses' if these options are used."
            )

        if len(self.data_type) > 1 and any(
            [name in ["all", "all_data_type"] for name in self.data_type]
        ):
            utils.log_and_raise_error(
                "'data_type' must only include 'all' or 'all_data_type' if these options are used."
            )

    # -----------------------------------------------------------------------------
    # Format Arguments
    # -----------------------------------------------------------------------------

    def get_processed_names(
        self,
        names_checked: List[str],
        sub: Optional[str] = None,
    ):
        """
        Process the list of subject session names.
        If they are pre-defined (e.g. ["sub-001", "sub-002"])
        they will be checked and formatted as per
        formatting.check_and_format_names() and
        any wildcard entries searched.

        Otherwise, if "all" or a variant, the local or
        remote folder (depending on upload vs. download)
        will be searched to determine what files exist to transfer,
        and the sub / ses names list generated.

        Parameters
        ----------

        see transfer_sub_ses_data()

        """
        if sub is None:
            sub_or_ses = "sub"
            search_prefix = self.cfg.sub_prefix + "-"
        else:
            sub_or_ses = "ses"
            search_prefix = self.cfg.ses_prefix + "-"

        if names_checked in [["all"], [f"all_{sub_or_ses}"]]:
            processed_names = folders.search_sub_or_ses_level(
                self.cfg,
                self.base_dir,
                self.local_or_remote,
                sub,
                search_str=f"{search_prefix}*",
            )[0]

            if names_checked == ["all"]:
                processed_names += [f"all_non_{sub_or_ses}"]

        else:
            processed_names = formatting.check_and_format_names(
                self.cfg, names_checked, sub_or_ses
            )
            processed_names = folders.search_for_wildcards(
                self.cfg,
                self.base_dir,
                self.local_or_remote,
                processed_names,
                sub=sub,
            )

        return processed_names

    def transfer_non_data_type(self, data_type_checked: List[str]) -> bool:
        """
        Convenience function, bool if all non-data-type folders
        are to be transferred
        """
        return any(
            [
                name in ["all_ses_level_non_data_type", "all"]
                for name in data_type_checked
            ]
        )
