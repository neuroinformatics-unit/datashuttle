# Getting Started

DataShuttle is a tool to streamline the management and standardisation of neuroscience project folders and files.

DataShuttle's goal is to alleviate the burden researchers face in adhering to standardised file and folder specifications during the execution of intricate and demanding experimental projects. It will:

- Eliminate the need to manually integrate datasets collected across different machines (e.g. *behaviour* and *electrophysiology* acquisition machines).
- Allow convenient transfer of data between machines. This may be between a central project storage and analysis machine (e.g. ''*I want to transfer subjects 1-5, sessions 5 and 10, behavioural data only to my laptop*.'')
- Avoid re-naming and re-formatting of project folders for collaboration or dataset publication.

DataShuttle aims to integrate seamlessly into existing neuroscience data collection and analysis workflows, providing tools to:

- Create folder trees that adhere to [SWC-Blueprint](https://swc-blueprint.neuroinformatics.dev/), a data management specification aligned to the Brain Imaging Dataset Specification (BIDS), widely used in neuroscience.
- Transfer data between machines used for data collection or analysis, and a central storage repository.

<img src="https://github.com/neuroinformatics-unit/datashuttle/assets/29216006/51b65a6d-492a-4047-ae7b-16273b58e258" alt="datashuttle central and local machines" class="img-responsive"/>


DataShuttle requires a [one-time setup](#initial-setup-with-configurations) of project name and configurations.  Next, subjects, session and data-type folder trees can be [created](#creating-subject-and-session-folders) during experimental acquisition.

Once acquisition is complete, data can be easily [transferred](#data-transfer) from acquisition computers to a central storage machine.

# Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle additionally requires Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.


# Setup

Datashuttle provides a cross-platform command line interface (CLI) used in the examples below, and a [Python API](#python-api-guide). Full references for the CLI ([CLI Reference](https://datashuttle.neuroinformatics.dev/pages/cli_index.html)) and API ([API Reference](https://datashuttle.neuroinformatics.dev/pages/api_index.html)) are available.

The first thing to do when using DataShuttle is to setup a new project on a *local* machine.

## *local* machines and the *central* machine

DataShuttle makes the distinction between (possibly multiple) *local* machines and a single *central* machine. DataShuttle needs to be setup once for each *local* machine, but requires no setup on the *central* machine.

A typical use case is an experiment in which _behavioural_ data and _electrophysiological_ data are collected on acquisition PCs. They send the data to a central server where it is stored.

Later, a subset of the data is transferred to a third machine for analysis. In this case, the _behavioural_ and _electrophysiological_ acquisition machine and analysis machines are _local_ . The central storage machine is the *central* machine.

## Initial setup with _configurations_

A one-time setup on each *local* machine used is required, specifying the *project name* and *configurations*.

The _configurations_ tell DataShuttle:

- The paths to the *local* and *central* folders that contain the project.
- How to connect to the _central_ machine.
- The settings that specify how data is transferred.
- The *datatypes* that will be used in the project, e.g. *behaviour* (`behav`) or *electrophysiology* (`ephys`).

The command `make-config-file` is used for the initial setup of the project. The **required arguments** are:

`local_path`: The full file-path to the project folder on the *local* machine. For example, if you wanted to make a new project called `my_first_project` in the folder `C:\User\my_projects`, the local path would be `C:\User\my_projects`.

`central_path`: The path on the *central* machine to the central project. For example, if connecting to a remote Linux server, this may be `/hpc/home/user/my_projects`.

`connection_method`: `local_filesystem` or `ssh`. Local filesystem can be used if the *central* storage is mounted to the local machine. Otherwise `ssh` can be used.

Finally, the *datatype* flags `--use_ephys`, `--use_funcimg`, `--use_histology`, `--use_behav` set the types of data required for the project on the local machine. While individual flags are optional, at least one must be chosen when initialising the project.

### Optional Arguments

If connection method is `ssh`, the `central_host_id`, `central_host_username` must be set, and a one-time SSH setup command run (see the [SSH section](#ssh) for details).

The optional arguments `overwrite_old_files`, `transfer_verbosity` and `show_transfer_progress` determine how *data transfer* is performed (see the [Data Transfer](#data-transfer) section for details).

### Example

An example call to `make-config-file` below creates a new project called `my_first_project`, sets the *local* project path to `/path/to/my/project`, the *central* path (to a remote Linux server) to `/nfs/nhome/live/username/`, the required SSH configurations, and indicates that *behavioural*, _electrophysiological_ and *histological* data will be used on this machine for this project.

Note that in the terminal, ``\`` indicates a new-line (allowing a single command to be spread across multiple lines for display purposes). On Windows, the `^` character is used instead.

```
datashuttle \
my_first_project \
make-config-file \
/path/to/my/project \
/nfs/nhome/live/username/ \
ssh \
--central_host_id ssh.swc.ucl.ac.uk \
--central_host_username username \
--transfer_verbosity v \
--use-ephys --use-behav --use-histology --overwrite_old_files
```


Now setup is complete! _Configuration_ settings can be edited at any time with the `update-config` command. Alternatively, custom *configuration* files can be supplied using the `supply-config` command (this simplifies setting up projects across multiple *local* machines).

Next, we can start setting up the project by automatically creating standardised project folder trees.

## Creating *subject* and *session* folders

In a typical neuroscience experiment, a data-collection session begins by creating the folder for the current subject (e.g. mouse, rat) and current session. Once created, the data for this session is stored in the created folder.

The command `make-sub-folders` can be used automatically create folder trees that adhere to the [SWC-Blueprint](https://swc-blueprint.neuroinformatics.dev/) specification. The linked specifications contain more detail, but at it's heart this requires:

- All subjects are given a numerical (integer) number that is prefixed with the key `sub-`.
- All sessions are also given a numerical (integer) number that is prefixed with the key `ses-`.

Following this, optional information can be included in the form of key-value pairs. For example, a folder tree for *subject 1*, *session 1*  with *behavioural* data that includes the date of the session in the *session* folder name would be:

```
└── sub-001/
    └── ses-001_date-20230516/
        └── behav/
            └── sub-001_ses-001_camera-top.mp4
```

In DataShuttle, this folder tree (excluding the .mp4 file which must be saved using third-party software) can be created (assuming today's date is `20220516`), with the command

```
datashuttle \
my_first_project \
make-sub-folders -sub 001 -ses 001_@DATE@ -dt behav
```

The leading `sub-` or `ses-` is optional when specifying folders to create (e.g. both `-sub 001` and `-sub sub-001` are valid inputs). It is possible to automatically create date, time or datetime key-value pairs with the days `@DATE@`, `@TIME@` or `@DATETIME@` respectively (see the [below section](#automatically-include-date-time-or-datetime
) for more detail).

Another example call, which creates a range of subject and session folders, is shown below:

```
datashuttle \
my_first_project \
make-sub-folders -sub 001@TO@003 -ses 010_@TIME@ -dt all
```

When the `all` argument is used for `--data_type` (`-dt`), the folders created depend on the *datatypes* specified during *configuration* setup. For example, if
`--use_behav`, `--use_funcimg`, `--use_histology` were set during *configuration* setup, the folder tree from the above command (assuming the time is `4.02.48 PM`), would look like:

```
├── sub-001/
│   ├── ses-010_time-160248/
│   │   ├── behav
│   │   └── funcimg
│   └── histology
├── sub-002/
│   ├── ses-010_time-160248/
│   │   ├── behav
│   │   └── funcimg
│   └── histology
└── sub-003/
    ├── ses-010_time-160248/
    │   ├── behav
    │   └── funcimg
    └── histology
```


### Data Types Folders

In [SWC-Blueprint](https://swc-blueprint.neuroinformatics.dev/specification.html), *datatypes* specify where acquired experimental data of currently supported types (`behav`, `ephys`, `funcimg` and `histology`) is stored. See the [*datatypes* section of the SWC-Blueprint for more details](https://swc-blueprint.neuroinformatics.dev/specification.html#datatype).

At present, `histology` is saved to the `sub-` level, as it is assumed `histology` is conducted *ex vivo* and so session will be possible. Please don't hesitate to get into contact if you have an alternative use case.

## Data Transfer

Once a local machine is setup, created folders can be filled with acquired experimental data. Once data collection is complete, it is often required to transfer this data to a central storage machine. This is especially important if data of different types (e.g. *behaviour*, *electrophysiology*) is acquired across multiple local machines.

DataShuttle offers a convenient way of transferring entire project folders, or subsets of data. For example, the call

```
datashuttle \
my_first_project \
upload \
-sub 001@TO@003 \
-ses 005_date-@*@ 006_date-@*@* \
-dt behav
```

Will *upload* (from *local* to *central* ) _behavioural_ _sessions_ 5 and 6, collected at any date, for _subjects_ 1 to 3.

The keyword `all` can be input in place of a `-sub`, `-ses` or _datatype_ argument `-dt` to transfer all available subject, sessions or data types available. For example:

```
datashuttle \
my_first_project \
download \
-sub all \
-ses 005 \
-dt ephys
```
Will transfer *electrophysiology* data of the 5th sessions for *all* subjects found on the *central* machine.

The *download* command transfers data from the *central* to *local* PC. This can be useful in case you want to analyse a subset of data that is held in *central* storage.

The main data transfer commands are: `upload`, `download`, `upload-all`, `download-all`, `upload-entire-project`, `download-entire-project`. To understand their behaviour, it is necessary to understand the concept of the *top-level folder*.

### Understanding the 'Top Level Folder' and Transfer Methods

SWC-Blueprint defines two main *top-level folders*, `rawdata` and `derivatives`. The purpose of `rawdata` is to store data directly as acquired. The `derivatives` folder is used to store the results of processing the `rawdata`. This distinction ensures that `rawdata` is not overwritten during processing, and makes sharing of `rawdata` simpler.

```
└── my_first_project/
    ├── rawdata/
    │   └── ...
    └── derivatives/
        └── ...
```

In DataShuttle, the current working *top level folder* is by default `rawdata`. The working *top level folder* determines where folders are created (e.g. `make_sub_folders`), and from which folder data is transferred.

For example, `upload` or  `upload-all` will transfer data with `rawdata` from *local* to *central*, if `rawdata` is the current *top-level folder*. `upload` transfers the specified subset of folders, while `upload-all` will upload the entire *top-level folder*.

To change the *top-level folder*, the command `set-top-level-folder` can be used. e.g.

```
datashuttle my_first_project set-top-level-folder derivatives
```

The *top-level folder* setting will remain across DataShuttle sessions.

After this change, *upload* or `upload-all` will transfer data in the `derivatives` folder.

To see the current *top-level folder*, the command `show-top-level-folder` can be used.

### Transferring the entire project

If you want to quickly transfer an entire project (i.e. all data in both `rawdata` and `derivatives`), the command `upload-entire-project` or `download-entire-project` can be used.

e.g. the command
`datashuttle my_first_project upload-entire-project`

run on the folder tree:

```
.
└── my_first_project/
    ├── rawdata/
    │   └── sub-001/
    │       └── ses-001/
    │           └── my_tracking_video.mp4
    └── derivatives/
        └── sub-001/
            └── tracking_video_results.csv
```

will transfer all data in both the `rawdata` and `derivatives` folders from the *local* machine to the *central* machine.

### Transferring files that are not within datatype folders

In some cases, files related to metadata may be stored outside of *datatype* folders.  When the `all` flag is used, files outside of folders at the *top-level folder* (for `-sub`), *subject* level (for `-ses`) and *session* level (`for -dt`) will also be transferred. However, if specific subject, session or datatype are selected, files outside of these will not be transferred.

The example below exemplifies how the `all` argument works during data transfer. For example, given the project folder:

```
└── rawdata/
    ├── sub-001/
    │   ├── sub-001_extrafile-sub.json
    │   └── ses-001/
    │       ├── sub-001_ses-001_extrafile-ses.json
    │       ├── behav/
    │       │   └── ...
    │       └── sub-001_ses-001_extrafile-dtype.json
    └── a_project_file.json
```

The command:

```
datashuttle \
my_first_project \
upload \
-sub all \
-ses-001 \
-dt all

```

will move:

- The file `a_project_file.json` (and any other files at this level) and search all *subjects* for the specified *sessions* */ datatypes*.

- Only *sessions* called `001`, but not any other files or folders at this level (i.e. `sub-001_ses-001_extrafile-ses.json` will not be transferred).

- All *datatypes* and non-*datatypes* at the session level. For example, `behav` and `sub-001_ses-001_extrafile-dtype.json` (that reside in *session* folders called `ses-001`) will be transferred.

For convenience, it is suggested to keep all files within *datatype* level folders. However, the `all` argument, as well as the additional available arguments: `all_sub` and `all_non_sub` (for `-sub`), `all_ses` and `all_non_ses` (for `-ses`) and `-all_ses_level_non_data_type` are available, as [detailed below](#flexible-transfers-with-keyword-arguments)


### Transferring a specific file or folder

The functions `upload-specific-folder-or-file` or `download-specific-folder-or-file` can be used to transfer an individual file or folder. The path to the file or folder (either full or relative to the working *top-level folder*) should be input.


## Summary

This concludes the *Get Started* part of the documentation. Hopefully, you are now equipped to manage an experimental project folder aligned to community standards with a few short commands.

Continue reading the documentation for a full overview of DataShuttle functionalities.

To discuss, contribute or give feedback on DataShuttle, please check out our discussions page and GitHub repository. Any feedback is welcomed and greatly appreciated!



# Advanced Usage


## Python API Guide

DataShuttle can be used through the command line interface (as exampled in the *Get Started* section) or through a Python API. All commands shown in the *Get Started* guide can be used similarly in the Python API (with hyphens replaced by underscores).

To start a project in Python, import DataShuttle and initialise the project class:

```
from datashuttle.datashuttle import DataShuttle

project = DataShuttle("my_first_project")
```

The configuration file can be setup similarly to the *Get Started* example:
```
project.make_config_file(
	local_path="/path/to/my/project",
	central_path="/nfs/nhome/live/username/",
	connection_method="ssh",
	central_host_id="ssh.swc.ucl.ac.uk",
	central_host_username="username",
	overwrite_old_files=True,
	transfer_verbosity="v",
	use_ephys=True,
	use_behav=True,
	use_histology=True,
)
```

and methods for making subject folders and transferring data accessed similarly. Note that the shortcut arguments `-sub`, `-ses`, `-dt` are not available through the Python API, and the full argument names (`sub_names`, `ses_names`, `data_type`) must be used.

```
project.make_sub_folders(
	sub_names="sub-001@TO@002",
	ses_names="ses-001_@DATE@",
	data_type="all"
)
```

```
project.upload(
	sub_names="001@TO@003",
	ses_names=["005_date-@*@", "006_date-@*@"],
	data_type="behav"
)
```

## Setting up the connection to *central*

### Local Filesystem

Local filesystem transfers are typically used when the *central* machine is setup as a mounted drive. This is a common form of communication between client machines and a central server, such as a high-performance computer (HPC, also often called *clusters*).

When a *central* machine is mounted to the *Local* machine, it acts as if is available as a local-filesystem folder. In this case, the `central_path` configuration (see `make_config_file`) can simply be set to the path directing to the mounted drive.

With the `connection_method` set to `local_filesystem`, data transfer will proceed between the *local* machine filesystem and mounted drive.

### SSH

One method of connecting with the *central* machine is the Secure Shell (SSH) protocol, that enables communication between two machines. In DataShuttle, SSH can be used as a method of communication between *local* and *central* machines.

The convenience command `setup-ssh-connection-to-central-server` can be used to setup an SSH connection to the *central* machine. The *central* machine must be a Linux-managed remote server. This command is only required to be run once.

This command requires that all configurations related to SSH communication (`central_host_id`, `central_username`) are set (using `make-config-file`). Running `setup-ssh-connection-to-central-server` will require verification that the SSH server connected to is correct (pressing `y` to proceed). Following this, your password to the *central* machine will be requested.

This command sets up SSH key pairs between *local* and *central* machines. Password-less SSH communication is setup and no further configuration should be necessary for SSH transfer.

In DataShuttle, the `connection_method` configuration must be set to `"ssh"` to use the SSH protocol for data transfers.

## Convenience tags

### Automatically include Date, Time or Datetime
*Used when making subject or session folders*

When creating subject or session folders, it is often desirable to include the *date*, *time*, or *datetime* as a key-value pair in the folder name. For example:

`ses-001_date-20230516`

DataShuttle provides convenience tags to automatically format a key-value pair with the current date or time (as determined from the machine *datetime*).

For example, the command:

```
datashuttle \
my_first_project \
make_sub_folders \
-sub sub_001@DATE@ \
-ses 001@TIME@ 002@DATETIME@
-dt behav
```

will create the folder tree (assuming the *top-level folder* is `rawdata`):

```
└── rawdata/
    └── sub-001_date-20230606/
        ├── ses-001_time-202701/
        │   └── behav
        └── ses-002_date-20230606_time-202701/
            └── behav
```


### Specify ranges with the `@TO@` flag
*When making subject or session folders and transferring data*

Often it is desirable to specify a range of subject or session names to make folders for, or transfer.

For example, in a project with 50 subjects (`sub-001`, `sub-002`, `...`, `sub-050`), it may be desired to transfer the first 25 subjects. This can be achieved using the `TO` flag, for example:

```
datashuttle \
my_first_project \
upload \
-sub 001@TO@025 \
-ses all \
-dt all
```


Note when making folders with the `@TO@` tag, the maximum number of leading zeros found either side of the tag will be used for folder creation. For example, in the call:

```
datashuttle \
my_first_project \
make_sub_folders \
-sub 0001@TO@02
```

will create the subject folders `sub-0001` and `sub-0002`.

### The wildcard flag `@*@`
*Used when transferring data*

When specifying the names of subjects or sessions to transfer, we often want to ignore matching portions of the name which may un-predictable. For example, we may be interested in a particular session across experimental subjects, for example the 5th session, that was run on a different day for each subject. For example, consider two subjects whose test session 5 was collected on different days:

```
└── rawdata/
    ├── sub-001  /
    │   ├── ...
    │   └── ses-005_condition-test_date-20230428/
    │       └── behav
    └── sub-002/
        └── ses-005_condition-test_date-20230431/
            └── behav
```

We can use the wildcard tag to match everything that comes after the `date` key. For example, to upload the these sessions from *local* to *central*, we can perform:
```
datashuttle \
my_first_project \
upload \
-sub 001 002
-ses 005_condition-test_date-@*@
-dt behav
```

Which would selectively upload session 5 from subjects 1 and 2.

If using macOS (or, in general, the `z-shell (zsh)`, names including the `@*@` flag must be wrapped in quotation marks, for example `--ses "005_condition-test_date-@*@"`.

Similarly, if the test session was on different session numbers for different sessions, we could use `-ses @*@condition-test@*@` (as the `-ses` argument above) to selectively transfer test sessions only.


## Data Transfer Options

Behind the scenes, DataShuttle uses the software [Rclone](https://rclone.org/) to transfer data. A number of Rclone options are exposed in DataShuttle to allow for more flexible data transfer. These are set in the *configurations* during project initialisation and can be edited with the command `update-config`.

### Overwriting existing files

The most important optional configuration, `overwrite_old_files` determines whether folders and files are overwritten during transfer. By default, DataShuttle does not overwrite during data transfer.

For example, if the file `sub-001_ses-001_measure-trajectories.csv` has been transferred from *local* to the *remote* repository, it will never be over-written in the *remote* repository. If the file is edited locally, such that the timestamp on the file is more recent in *local* compared to *remote*, the *remote* version will still not be overwritten.

To change this behaviour, the configuration `overwrite_old_files` can be set to `True`. In this case, files in which the timestamp of the target directory (e.g. *central* when performing `upload`) will be overwritten if their timestamp is older than the corresponding file in the source directory (e.g. *local* when performing `upload`.
)

### Additional Transfer Configurations

`transfer_verbosity` : set to `"vv"` for a extensive detail on the transfer operation. Set to `"v"` to only see each file that is transferred as well as significant events that occur during transfer.

`show_transfer_progress` : When `True`, real-time transfer statistics will be reported and logged.

### Flexible transfers with keyword arguments

DataShuttle provides a number of keyword arguments to allow separate handling of files that are not found in *datatype* folders.

#### For use with the `-sub` / `--sub-names` flag

`all` : All *subject* and non-*subject* files and folders within the *top-level folder* (e.g. `rawdata`) will be transferred.

`all_sub` : *Subject*  <u>folders</u> only (i.e. prefixed with `-sub`) will be transferred.

`all_non_sub` : All files and folders that are not prefixed with `-sub` will be transferred. Any folders prefixed with `-sub` will not be transferred.

#### For use with the `-ses` / `--ses-names` flag

`all` : All *session* and non-*session* files and folders within a *subject* level folder (e.g. `sub-001`) will be transferred.

`all_ses` : *Session* <u>folders</u> only (i.e. prefixed with `-ses`) will be transferred. Note that the only exception is the `histology` folder, the transfer of which is determined by the `-dt` flag (below).

`all_non_ses` : All files and folders that are not prefixed with `-sub` will be transferred. Any folders prefixed with `-ses` will not be transferred.

#### For use with the `-dt` / `--datatype` flag

`all` : All *datatype* folders at the *subject* or *session* folder level will be transferred, as well as all files and folders within selected *session* folders.

`all_data_type` : All *datatype* folders (i.e. folders with the pre-determined name: `behav`, `ephys`, `funcimg`, `histology`) residing at either the *subject* or *session* level will be
transferred. Non-*datatype* folders at the *session* level will not be transferred

`all_ses_level_non_data_type` : Non *datatype* folders at the *session* level will not be transferred

Below, a number of examples are given to exemplify how these arguments effect data transfer. Given the *local* project folder:

```
.
└── rawdata/
    ├── a_project_related_file.json
    ├── sub-001/
    │   ├── sub-001_extra-file.json
    │   ├── histology
    │   └── ses-001/
    │       ├── ses-001_extra-file.json
    │       ├── behav/
    │       │   └── ...
    │       └── ephys/
    │           └── ...
    └── sub-002/
        ├── sub-002_extra-file.json
        ├── histology
        └── ses-001/
			├── behav/
			│   └── ...
			└── ephys/
				└── ...
```

1) The first example indicates the effect of selectively transferring non-*datatype* sessions. The command:

```
datashuttle \
my_first_project \
upload
-sub all
-ses all
-dt all_ses_level_non_data_type
```

Would upload:

- All non-*subject* files in the *top-level* folder (`rawdata`)
- The `sub-001_extra_file.json` and `sub-002_extra_file.json`
- For `sub-001`, the file `ses-001_extra_file.json`. For `sub-002`, no other files are transferred because there is no non-*datatype* files at the *session* level.


2) The next two examples show the effect of selecting `-dt all` vs. `-dt all_data_type`. The command:

```
datashuttle \
my_first_project \
upload
-sub 001
-ses all_non_ses
-dt all
```

Would upload:

- Contents residing in the `sub-001` folder only.
-  The file `sub-001_extra-file.json`
- All *datatype* folder contents (`histology`, `behav`, `ephys`)

The command:

```
datashuttle \
my_first_project \
upload
-sub 001
-ses all_sub
-dt all_data_type
```

Would upload:

- Contents residing in the `sub-001` folder only.
- All *datatype* folder contents (`histology`, `behav`, `ephys`)

3) The final example shows the effect of transferring `all_non_sub` files only. The command:

```
datashuttle \
my_first_project \
upload
-sub all_non_sub
-ses all
-dt all
```

Would upload:

- the file `a_project_related_file.json` only.

## Query DataShuttle for current *configurations*

It is possible to query DataShuttle for the current *configurations* and relevant file paths,
for example the `show-local-path` command will print the currently set *local* path to the terminal.

Similarly, the command `show-configs` will print all currently set *configurations*. A number of additional convenience functions exist (for example `show-remote-path`, `show-top-level-folder`, `show-config-path`). For a full list, see our [CLI reference](https://datashuttle.neuroinformatics.dev/pages/cli_index.html) or [API reference](https://datashuttle.neuroinformatics.dev/pages/api_index.html).

## Logging

Detailed logs of all configuration changes, folder creation and data transfers are logged
to the `.datashuttle` folder that is created in the *local* project folder.

For each command run, a log of that command is placed in the logs folder, with the time and date of the command. The log itself contains relevant information pertaining to that command. For example, if the commands `make_sub_folders`, `upload`, `download` were run sequentially, the logs output folder would look like:

```
make_sub_folders_2023-06-08_09-55-14.log
upload_data_2023-06-08_09-55-45.log
download_data_2023-06-08_09-56-19.log
```
