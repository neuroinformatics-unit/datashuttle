from pathlib import Path, PosixPath
from typing import List, Literal, Optional, Tuple, Union

from datashuttle.configs import canonical_folders
from datashuttle.configs.config_class import Configs
from datashuttle.utils import folders, formatting, rclone, utils
from datashuttle.utils.custom_types import (
    OverwriteExistingFiles,
    Prefix,
    TopLevelFolder,
)


class TransferData:
    """
    Class to perform data transfers. This works by first building
    a large list of all files to transfer. Then, rclone is called
    once with this list to perform the transfer.

    The properties on this class are to be read during generation
    of transfer lists and should never be changed during the lifetime
    of the class.

    Parameters
    ----------

    cfg : Configs,
        datashuttle configs UserDict.

    upload_or_download : Literal["upload", "download"]
        Direction to perform the transfer.

    top_level_folder: TopLevelFolder

    sub_names : Union[str, List[str]]
        List of subject names or single subject to transfer. This
        can include transfer keywords (e.g. "all_non_sub").

    ses_names : Union[str, List[str]]
        List of sessions or single session to transfer, for each
        subject. May include session-level transfer keywords.

    datatype : Union[str, List[str]]
        List of datatypes to transfer, for the sessions / subjects
        specified. Can include datatype-level tranfser keywords.

    overwrite_existing_files : OverwriteExistingFiles
        If "never" files on target will never be overwritten by source.
        If "always" files on target will be overwritten by source if
        there is any difference in date or size.
        If "if_source_newer" files on target will only be overwritten
        by files on source with newer creation / modification datetime.

    dry_run : bool,
        If `True`, transfer will not actually occur but will be logged
        as if it did (to see what would happen for a transfer).

    log : bool,
        if `True`, log and print the transfer output.
    """

    def __init__(
        self,
        cfg: Configs,
        upload_or_download: Literal["upload", "download"],
        top_level_folder: TopLevelFolder,
        sub_names: Union[str, List[str]],
        ses_names: Union[str, List[str]],
        datatype: Union[str, List[str]],
        overwrite_existing_files: OverwriteExistingFiles,
        dry_run: bool,
        ignore_files: Union[str, List[str]] = "",
        log: bool = True,
    ):
        self.__cfg = cfg
        self.__upload_or_download = upload_or_download
        self.__top_level_folder = top_level_folder
        self.__local_or_central = (
            "local" if upload_or_download == "upload" else "central"
        )
        self.__base_folder = self.__cfg.get_base_folder(
            self.__local_or_central, self.__top_level_folder
        )

        self.sub_names = self.to_list(sub_names)
        self.ses_names = self.to_list(ses_names)
        self.datatype = self.to_list(datatype)
        self.ignore_files = self.to_list(ignore_files) if ignore_files else []

        self.check_input_arguments()

        include_list, exclude_list = (
            self.build_a_list_of_all_files_and_folders_to_transfer()
        )

        transfer_file = self.make_transfer_arg(include_list, exclude_list)

        if any(include_list):
            output = rclone.transfer_data(
                self.__cfg,
                self.__upload_or_download,
                self.__top_level_folder,
                transfer_file,
                cfg.make_rclone_transfer_options(
                    overwrite_existing_files, dry_run
                ),
            )

            self.reset_transfer_file()

        if log:
            message = (
                output.stderr.decode("utf-8")
                if any(include_list)
                else "No files included. None transferred."
            )
            utils.log_and_message(message)

    # -------------------------------------------------------------------------
    # Build the --filter-from list
    # -------------------------------------------------------------------------

    def build_a_list_of_all_files_and_folders_to_transfer(
        self,
    ) -> Tuple[List[str], List[str]]:
        """
        Build a list of every file to transfer based on the user-passed
        arguments. This cycles through every subject, session and datatype
        and adds the outputs to three lists:

        `sub_ses_dtype_include` - files within datatype folders
        `extra_folder_names` - folders that do not fall within datatype folders
        `extra_file_names` - files that do not fall within datatype folders

        Returns
        -------

        include_list : List[str]
            A list of paths to pass to rclone's `--include` flag.
        """
        # Find sub names to transfer
        processed_sub_names = self.get_processed_names(self.sub_names)

        sub_ses_dtype_include: List[str] = []
        extra_folder_names: List[str] = []
        extra_filenames: List[str] = []
        exclude_list: List[str] = []

        for sub in processed_sub_names:
            # subjects at top level folder ------------------------------------

            if sub == "all_non_sub":
                self.update_list_with_non_sub_top_level_folders(
                    extra_folder_names, extra_filenames
                )
                continue

            self.update_list_with_dtype_paths(
                sub_ses_dtype_include,
                self.datatype,
                sub,
            )

            # sessions at sub level folder ------------------------------------

            processed_ses_names = self.get_processed_names(self.ses_names, sub)

            for ses in processed_ses_names:
                if ses == "all_non_ses":
                    self.update_list_with_non_ses_sub_level_folders(
                        extra_folder_names, extra_filenames, sub
                    )

                    continue

                # Datatype (sub and ses level) --------------------------------

                if self.transfer_non_datatype(self.datatype):
                    self.update_list_with_non_dtype_ses_level_folders(
                        extra_folder_names, extra_filenames, sub, ses
                    )

                self.update_list_with_dtype_paths(
                    sub_ses_dtype_include,
                    self.datatype,
                    sub,
                    ses,
                )

        include_list = (
            self.make_include_arg(
                sub_ses_dtype_include, exclude_files=any(self.ignore_files)
            )
            + self.make_include_arg(
                extra_folder_names, exclude_files=any(self.ignore_files)
            )
            + self.make_include_arg(
                extra_filenames,
                recursive=False,
                exclude_files=any(self.ignore_files),
            )
        )

        if self.ignore_files:
            excluded_files, excluded_folders = (
                self.update_list_with_excluded_paths(
                    self.ignore_files,
                    sub_ses_dtype_include=sub_ses_dtype_include,
                    extra_folder_names=extra_folder_names,
                    extra_filenames=extra_filenames,
                )
            )

            exclude_list = self.make_exclude_arg(
                excluded_folders
            ) + self.make_exclude_arg(excluded_files, recursive=False)

        return include_list, exclude_list

    def make_include_arg(
        self,
        list_of_paths: List[str],
        recursive: bool = True,
        exclude_files: bool = False,
    ) -> List[str]:
        """
        Format the list of paths to rclone's required
        `--include` flag format.
        """
        if not any(list_of_paths):
            return []

        if recursive:

            def include_arg(ele: str, exclude_files: bool = False) -> str:
                if exclude_files:
                    return f" + {ele}/** "
                return f' --include "{ele}/**" '

        else:

            def include_arg(ele: str, exclude_files: bool = False) -> str:
                if exclude_files:
                    return f" + {ele} "
                return f' --include "{ele}" '

        return [include_arg(ele, exclude_files) for ele in list_of_paths]

    def make_exclude_arg(
        self, list_of_paths: List[str], recursive: bool = True
    ) -> List[str]:
        """
        Format the list of paths to rclone's required
        `--exclude` flag format.
        """
        if not any(list_of_paths):
            return []

        if recursive:

            def exclude_arg(ele: str) -> str:
                return f" - {ele}/** "

        else:

            def exclude_arg(ele: str) -> str:
                return f" - {ele} "

        return [exclude_arg(ele) for ele in list_of_paths]

    def make_transfer_arg(
        self, include_files: List[str], exclude_files: List[str]
    ) -> List[str]:
        """
        Format the list of paths to rclone's required
        `--filter-from` flag format.
        """
        if exclude_files:
            ignore_path: PosixPath = self.write_transfer_file(
                include_files, exclude_files
            )
            return [f' --filter-from "{ignore_path}" ']

        return ["".join(include_files)]

    def write_transfer_file(
        self, include_files: List[str], exclude_files: List[str]
    ) -> PosixPath:
        """
        Write the list of files to transfer to a file
        """
        file_path: PosixPath = self.get_datashuttle_ignore_path(self.__cfg)

        with open(file_path, "w") as f:
            f.write("\n".join(exclude_files + include_files))
            f.write("\n - **")

        return file_path

    # -------------------------------------------------------------------------
    # Search for non-sub / ses / dtype folders and add them to list
    # -------------------------------------------------------------------------

    def update_list_with_non_sub_top_level_folders(
        self,
        extra_folder_names: List[str],
        extra_filenames: List[str],
    ) -> None:
        """
        Search the subject level for all files and folders in the
        top-level-folder. Split the output based onto files / folders
        within "sub-" prefixed folders or not.
        """
        top_level_folders: List[str]
        top_level_folders, top_level_files = folders.search_sub_or_ses_level(  # type: ignore
            self.__cfg,
            self.__cfg.get_base_folder(
                self.__local_or_central, self.__top_level_folder
            ),
            self.__local_or_central,
            search_str="*",
        )

        top_level_folders = list(
            filter(lambda folder: folder[:4] != "sub-", top_level_folders)
        )

        extra_folder_names += top_level_folders
        extra_filenames += top_level_files

    def update_list_with_non_ses_sub_level_folders(
        self,
        extra_folder_names: List[str],
        extra_filenames: List[str],
        sub: str,
    ) -> None:
        """
        For the subject, get a list of files / folders that are
        not within "ses-" prefixed folders.
        """
        sub_level_folders: List[str]
        sub_level_folders, sub_level_files = folders.search_sub_or_ses_level(  # type: ignore
            self.__cfg,
            self.__cfg.get_base_folder(
                self.__local_or_central, self.__top_level_folder
            ),
            self.__local_or_central,
            sub=sub,
            search_str="*",
        )
        sub_level_dtype = [
            dtype.name
            for dtype in canonical_folders.get_datatype_folders().values()
            if dtype.level == "sub"
        ]

        filt_sub_level_folders = filter(
            lambda folder: folder[:4] != "ses-"
            and folder not in sub_level_dtype,
            sub_level_folders,
        )
        extra_folder_names += [
            "/".join([sub, folder]) for folder in filt_sub_level_folders
        ]
        extra_filenames += ["/".join([sub, file]) for file in sub_level_files]

    def update_list_with_non_dtype_ses_level_folders(
        self,
        extra_folder_names: List[str],
        extra_filenames: List[str],
        sub: str,
        ses: str,
    ) -> None:
        """
        For a specific subject and session, get a list of files / folders
        that are not in canonical datashuttle datatype folders.
        """
        ses_level_folders: List[str]
        (
            ses_level_folders,
            ses_level_filenames,
        ) = folders.search_sub_or_ses_level(  # type: ignore
            self.__cfg,
            self.__cfg.get_base_folder(
                self.__local_or_central, self.__top_level_folder
            ),
            self.__local_or_central,
            sub=sub,
            ses=ses,
            search_str="*",
        )

        ses_level_dtype = [
            dtype.name
            for dtype in canonical_folders.get_datatype_folders().values()
            if dtype.level == "ses"
        ]
        filt_ses_level_folders = filter(
            lambda folder: folder not in ses_level_dtype, ses_level_folders
        )
        extra_folder_names += [
            "/".join([sub, ses, folder]) for folder in filt_ses_level_folders
        ]
        extra_filenames += [
            "/".join([sub, ses, file]) for file in ses_level_filenames
        ]

    # -------------------------------------------------------------------------
    # Update list with path to sub and ses level datatype folders
    # -------------------------------------------------------------------------

    def update_list_with_dtype_paths(
        self,
        sub_ses_dtype_include: List[str],
        datatype: List[str],
        sub: str,
        ses: Optional[str] = None,
    ) -> None:
        """
        Given a particular subject and session, get a list of all
        canonical datatype folders.
        """
        datatype = list(filter(lambda x: x != "all_non_datatype", datatype))

        datatype_items = folders.items_from_datatype_input(
            self.__cfg,
            self.__local_or_central,
            self.__top_level_folder,
            datatype,
            sub,
            ses,
        )

        level = "ses" if ses else "sub"

        for datatype_key, datatype_folder in datatype_items:  # type: ignore
            if datatype_folder.level == level:
                if ses:
                    filepath = Path(sub) / ses / datatype_folder.name
                else:
                    filepath = Path(sub) / datatype_folder.name

                sub_ses_dtype_include.append(filepath.as_posix())

    # -------------------------------------------------------------------------
    # Update list with files to exclude inside included transfer paths
    # -------------------------------------------------------------------------

    def update_list_with_excluded_paths(
        self,
        ignore_files: List[str],
        sub_ses_dtype_include: List[str],
        extra_folder_names: List[str],
        extra_filenames: List[str],
    ) -> Tuple[List[str], List[str]]:
        """
        Update the include list with the files to exclude
        from transfer. These are passed as a list of strings
        and will be formatted to rclone's `--filter-from` format.
        """

        ignored_extra_files: List[str] = []
        factually_ignored_files: List[str] = []
        ignored_sub_ses_files: List[str] = []
        factually_ignored_folders: List[str] = []

        if extra_filenames:
            ignored_extra_files += folders.search_for_ignore_extra_files(
                ignore_files,
                extra_filenames,
                self.__base_folder,
            )

        if sub_ses_dtype_include or extra_folder_names:
            factually_ignored_folders, ignored_sub_ses_files = (
                folders.search_for_ignore_files_in_folders(
                    ignore_files,
                    sub_ses_dtype_include,
                    extra_folder_names,
                    self.__base_folder,
                )
            )

        factually_ignored_files = ignored_extra_files + ignored_sub_ses_files

        return factually_ignored_files, factually_ignored_folders

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------

    def to_list(self, names: Union[str, List[str]]) -> List[str]:
        if isinstance(names, str):
            names = [names]
        return names

    def check_input_arguments(
        self,
    ) -> None:
        """
        Check the sub / session names passed. The checking here
        is stricter than for create_folders / formatting.check_and_format_names
        because we want to ensure that a) non-datatype arguments are not
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
                "'sub_names' must only include 'all' "
                "or 'all_subs' if these options are used.",
                ValueError,
            )

        if len(self.ses_names) > 1 and any(
            [name in ["all", "all_ses"] for name in self.ses_names]
        ):
            utils.log_and_raise_error(
                "'ses_names' must only include 'all' "
                "or 'all_ses' if these options are used.",
                ValueError,
            )

        if len(self.datatype) > 1 and any(
            [name in ["all", "all_datatype"] for name in self.datatype]
        ):
            utils.log_and_raise_error(
                "'datatype' must only include 'all' "
                "or 'all_datatype' if these options are used.",
                ValueError,
            )

        for name, list_ in zip(
            ["sub_names", "ses_names", "datatype"],
            [self.sub_names, self.ses_names, self.datatype],
        ):
            if len(list_) == 0:
                utils.log_and_raise_error(
                    f"`{name}` input cannot be empty.",
                    ValueError,
                )

    def get_datashuttle_ignore_path(self, cfg: Configs) -> PosixPath:
        """
        Return the path to the .datashuttleignore file
        """
        return cfg["local_path"] / ".datashuttle/.datashuttleignore"

    def reset_transfer_file(self) -> None:
        """
        Reset the .datashuttleignore file
        """
        with open(self.get_datashuttle_ignore_path(self.__cfg), "w") as f:
            f.write("")

    # -------------------------------------------------------------------------
    # Format Arguments
    # -------------------------------------------------------------------------

    def get_processed_names(
        self,
        names_checked: List[str],
        sub: Optional[str] = None,
    ) -> List[str]:
        """
        Process the list of subject session names.
        If they are pre-defined (e.g. ["sub-001", "sub-002"])
        they will be checked and formatted as per
        formatting.check_and_format_names() and
        any wildcard entries searched.

        Otherwise, if "all" or a variant, the local or
        central folder (depending on upload vs. download)
        will be searched to determine what files exist to transfer,
        and the sub / ses names list generated.

        Parameters
        ----------

        see transfer_sub_ses_data()

        """
        prefix: Prefix
        if sub is None:
            prefix = "sub"
        else:
            prefix = "ses"

        if names_checked in [["all"], [f"all_{prefix}"]]:
            processed_names: List[str]
            processed_names = folders.search_sub_or_ses_level(  # type: ignore
                self.__cfg,
                self.__base_folder,
                self.__local_or_central,
                sub,
                search_str=f"{prefix}-*",
            )[0]

            if names_checked == ["all"]:
                processed_names += [f"all_non_{prefix}"]

        else:
            processed_names = formatting.check_and_format_names(
                names_checked, prefix
            )
            processed_names = folders.search_for_wildcards(
                self.__cfg,
                self.__base_folder,
                self.__local_or_central,
                processed_names,
                sub=sub,
            )

        utils.log_and_message(
            f"The {prefix} names to transfer are: {processed_names}"
        )

        return processed_names

    def transfer_non_datatype(self, datatype_checked: List[str]) -> bool:
        """
        Convenience function, bool if all non-datatype folders
        are to be transferred
        """
        return any(
            [name in ["all_non_datatype", "all"] for name in datatype_checked]
        )
