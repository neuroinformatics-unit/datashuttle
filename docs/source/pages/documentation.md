# Full Documentation


DataShuttle is a tool to streamline the management and standardisation of neuroscience project folders and files.

DataShuttle's goal is to alleviate the burden researchers face in adhering to standardized file and folder specifications during the execution of intricate and demanding experimental projects. It will:

- Eliminate the need to manually integrate datasets collected across different machines (e.g. behaviour and electrophysiology acquisition machines).
- Allow convenient transfer of data between machines. This may be between a central project storage and analysis machine (e.g. ''*I want to transfer subjects 1-5, sessions 5 and 10, behavioural data only to my laptop*.'')
- Avoids re-naming and re-formatting of project folders for collaboration or dataset publication.

DataShuttle aims to integrate seamlessly into the  neuroscience data collection and analysis workflows and eliminate the need to manually , providing tools to:

- Create folder trees that adhere to SWC-Blueprint, a data management specification based on and aligned to the Brain Imaging Dataset Specification (BIDS), widely used in neuroscience.
- Convenient transfer of between machines used for data collection and analysis, and a central storage repository.

[IMAGE OF PCS]

DataShuttle requires a one-time setup of project name and configurations.  Next, subjects, session and data-type folder trees can be conveniently created during experimental acquisition. Once acquisition is complete, data can be easily transferred from acquisition computers to a central storage machine.

### Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle additionally requires Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.


### Getting Started

Datashuttle provides a Python API and cross-platform command line interface (CLI). In this guide examples will be down using the command line, but corresponding methods can be found in the [API Reference](https://datashuttle.neuroinformatics.dev/pages/api_index.html).

The first thing to do when using DataShuttle is to setup a new project on a *local* machine.

#### *local* machines and the *central* machine

DataShuttle makes the distinction between (possibly multiple) *local* machines and a single *central* machine. DataShuttle needs to be setup once for each *local* machine, but requires no setup on the *central* machine.

A typical use case is an experiment in which behavioural data and electrophysiological data are collected on acquisition PCs. They send the data to a central server where it is stored.

Later, a subset of the data is transferred to a third machine for analysis. In this case, the behavioural and electrophysiological acquisition machine and analysis machines are 'local'. The central storage machine is the *central* machine.

#### One-time project setup on a *local* machine

A one-time setup on each *local* machine used is required, specifying the *project name* and *configurations*.

The configurations tell DataShuttle

- The paths to the *local* and *central* folders that contain the project.
- How to connect to the central project.
- The settings that specify how data is transferred.
- The *data-types* (e.g. *behaviour* (`behav`), *electrophysiology* (`ephys`)) that will be used in the project.

The command `make-config-file` is used for the initial setup of the project. The **required arguments** are:

`local_path`: The full filepath to the project folder on the *local* machine. For example, if you wanted to make a new project called `my_first_project` in the folder `C:\User\my_projects`, the local path would be `C:\User\my_projects`.

`central_path`: The path on the *central* machine to the central project. For example, if connecting to a remote linux server, this may be `/hpc/home/user/my_projects`.

`connection_method`: `local_filesystem` or `ssh`. Local filesystem can be used if the *central* storage is mounted to the local machine. Otherwise `ssh` can be used.

Finally, the *data-type* flags `--use_ephys`, `--use_funcimg`, `--use_histology`, `--use_behav` set the types of data required for the project on the local machine. While individual flags are optional, at least one must be chosen when initialising the project.

**Optional Arguments**

If connection method is `ssh`, the `central_host_id`, `central_host_username` must be set, and a one-time SSH setup command run (see the [SSH section][#### SSH] for details).

The optional arguments `ovewrite_old_files`, `transfer_verbosity` and `show_transfer_progress` determine how *data transfer* is performed (see the [Data Transfer section](#### Data Transfer) for details).

**Example**

An example call to `make-config-file` below sets makes a new project called `my_first_project`, sets the *local* project path to `/path/to/my/project`, the *central* path (to a remote linux server) to `/nfs/nhome/live/username/`, sets the required SSH configurations, and indicates that *behavioural*, electrophysiological and *histological* data will be used on this machine for this project.

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


Now setup is complete! Configuration settings can be edited at any time with the `update-config` command (TODO LINK). Alternatively, custom confiruation files can be supplied using the `supply-config` command (TODO LINK) (this greatly simplifies setting up projects across multiple *local* machines).

Next, we can start setting up the project by automatically creating project folder trees that conform to a standardised specification.

#### Creating *subject* and *session* folders

In a typical neuroscience experiment, a data-collection session begins by creating the folder for the current subject name (e.g. mouse, rat) and current session name. Once created, the data for this session is stored in the created folder.

The command `make-sub-folders` can be used automatically create folder trees that adhere to the SWC-Blueprint (and correspondingly, BIDS) specification. The linked specifications contain more detail, but at it's heart this requires:

All subjects are given a numerical (integer) number that is prefixed with the key `sub-`. All sessions are also given a numerical (integer) number that is prefixed with the key `ses-`.

Following this, optional information can be included in the form of key-value pairs. For example, a folder tree for *subject 1*, *session 1*  with *behavioural* data that includes the date of each session in the *session* folder name would be:

```
└── sub-001/
    └── ses-001_date_20230516/
        └── behav/
            └── sub-001_ses-001_recording.mp4
```

In DataShuttle, this folder tree (excluding the .mp4 file which must be saved using third-party software) can be created (assuming today's date is `20220516`), with the command

```
datashuttle \
my_first_project \
make-sub-folders -sub 001 -ses 001_@DATE@ -dt behav
```

The leading `sub-` or `ses-` is optional when specifying folders to create. It is possible to automatically create date, time or datetime key-value pairs with the days `@DATE@`, `@TIME@` or `@DATETIME@` respectively.

Another example call, which creates a range of subject and session folders, is shown below:

```
datashuttle \
my_first_project \
make-sub-folders -sub 001@TO@003 -ses 010_@TIME@ -dt all
```

When the `all` argument is used for `--data_type` (`-dt`), the folders created depend on the *data-types* specified during *configuration* setup. For example, if
`--use_behav`, `--use_funcimg`, `--use_histology` were set during *configuration* setup, the folder tree from the above command (assuming the time is 4.02.48 PM), would look like:

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

# FOR FULL DETAILS, SEE XXX


#### Data Transfer



#### Configuration


This documentation gives examples both using the API (in the python console) or using the command line interface (in system terminal).

## DataShuttle Configs

### Configuration File

To get started, import DataShuttle and initialise the class with the project name. If using the command
line this step is not necessary.

```
from datashuttle.datashuttle import DataShuttle

project = DataShuttle("my_project")
```
The first time you use DataShuttle, you will be prompted to make a configuration file containing project information.

To setup the configuration, use the "make_config_file" function.

The "local_path" argument is required to specify the top-level path to your project. This will typically be empty
on first use, and should include the name of the project.

e.g. if the local_path="/path/to/my_project", when making a new subject (e.g. sub-001) this will be
made at /path/to/my_project/rawdata/sub-001.

Next, the "central_path" argument gives the path to the central machine project. This may be on a local
filesystem (e.g. if a HPC or network drive is mounted) or using SSH. On Linux systems, ~ syntax is
not supported and the full filepath must be input.

Also required is the "connection_method". This can either be "local_filesystem" or "ssh". If "ssh",
then the "central_host_id" and "central_host_username" options are also required (see example below).

The options "use_ephys", "use_behav"... are used to set the data types used on the local PC.
If these are not set to True, it will not be possible to make data_type folders of this type.
This option is useful if there are dedicated machines for collection of different data types.

Finally, the settings "overwrite_old_files", "transfer_verbosity" and "show_transfer_progress" determine
the behaviour during file transfer. Please see the Data Transfer section for more information.

An example call may look like:

```
project.make_config_file(
local_path="/path/to/my/my_project",
central_path="/nfs/nhome/live/username/",
connection_method="ssh",
central_host_id="ssh.swc.ucl.ac.uk",
central_host_username="username",
overwrite_old_files=True,
transfer_verbosity="v",
show_transfer_progress=False,
use_ephys=True,
use_behav=True,
use_histology=True
)
```
or equivalently using the command-line interface


```
datashuttle \
my_project \
make_config_file \
/path/to/my/project \
/nfs/nhome/live/username/ \
ssh \
--central_host_id ssh.swc.ucl.ac.uk \
--central_host_username username \
--transfer_verbosity v \
--use-ephys --use-behav --use-histology --overwrite_old_files
```

Individual settings can be updated using update_config(), and an existing config file can be used instead using supply_config()

### Setting up an SSH Connection

Once configurations are set, if the "connection_method" is "ssh", the function setup_ssh_connection_to_central_server() must be run to setup
the ssh connection to the central server. This will allow visual confirmation of the server key, and setup a SSH key pair. This means
your password will have to be entered only once, when setting up this connection.

## Making Project Folders

Subject and session project folders can be made using the function make_sub_folders(). This function accepts a subject name (or list
of subject names), with optional session name and data type inputs. If no session or data type name is provided,
an empty subject folder will be made at the top folder level.

The full paths of all created folders are logged (see "Logging" below).

e.g.
`project.make_sub_folders(sub_names="sub-001")` or equivalently `datashuttle my_project make_sub_folders --sub_names sub-001`

will make the folder tree

```
.
└── my_project/
    └── rawdata/
        └── sub-001
```

Adding a "ses_names" argument will make the specified sessions for all input subjects. Similarly, for each subject or session,
all data_types will be made. The data_type argument can be a single data_type (e.g. "behav"), a list of data_types or "all",
that will make all data_types. Note that in all cases, only data_types that are flagged to use in the configs (e.g. use_behav=True)
will be made.

All subject or session names must be prefixed with "sub-" or "ses-" respectively, as according to SWC-BIDS. If these prefixes
are not input, they will be automatically added. This method will also raise an error if the session number already exists,
and any duplicate inputs will be removed. Finally, subject and session names must not contain spaces and should be
formatted according to SWC-BIDS.
e.g.
```
project.make_sub_folders(
sub_names=["001", "002"],
ses_names=["ses-001", "002"],
data_type=["ephys", "behav", "histology"]
)
```
or equivalently

```
datashuttle \
my_project \
make_sub_folders \
--sub-names 001 002 \
--ses-names ses-001 002
--data_type ephys behav histology
```

will create the folder structure:

```
.
└── my_project/
    └── rawdata/
        ├── sub-001/
        │   ├── ses-001/
        │   │   ├── ephys
        │   │   └── behav
        │   ├── ses-002/
        │   │   ├── ephys
        │   │   └── behav
        │   └── histology
        └── sub-002/
            ├── ses-001/
            │   ├── ephys
            │   └── behav
            ├── ses-002/
            │   ├── ephys
            │   └── behav
            └── histology
```


### Convenience Tags

Tags can be added to easily format subject or session names. These tags include @TO@, @DATE@, @TIME@, @DATETIME@.

The @TO@ tag can be used to create a range of subjects or sessions. Where the subject or session number is
usually written, a range can be created by placing boundaries on the range either side of the @TO@ tag.
e.g. using sub_names=`sub-001@TO@003_task-retinotopy` would create three subject folders:
`sub-001_task-retinotopy, sub-002_task-retinotopy` and `sub-003_task-retinotopy`.

The @DATE@, @TIME@ or @DATETIME@ flags can be used to create date, time or datetime key-value pairs in subject or session
names, depending on the current system date / time. For example:

```
project.make_sub_folders(
sub_names="sub-001@TO@002",
ses_names="ses-001_@DATE@",
data_type=""
)
```
or equivalently

```
datashuttle \
my_project \
make_sub_folders \
--sub_names sub-001@TO@002 \
--ses_names ses-001_@DATE@ \
--data_type ""
```

would create the folder tree (assuming it is 01/02/2022)

```
.
└── my_project/
    └── rawdata/
        ├── sub-001/
        │   └── ses-001_date-01022022
        └── sub-002/
            └── ses-001_date-01022022
```
only one @DATE@, @TIME@ or @DATETIME@ flag can be used per subject / session name.

## Data Transfer

Data transfer can be either from the local project to the central project ("upload") or from the central to local project("download"). Data
transfers are primarily managed using the upload_data() and download_data() functions.

By default, uploading or downloading data will never overwrite files when transferring data. If an
existing file with the same name is found in the target folder, even if it is older, it will not be overwritten.
All transfer activity is printed to the console and logged (see "Logging" below), which can be used to
determine if any files were not transferred for this reason.

To transfer all data, the keyword "all" can be used for sub_names, ses_names and data_type arguments. Note that
any existing data_type will be transferred, even if the flag use_<data_type> (e.g. use_behav) is False.

For example, `project.upload_data(sub_names="all", ses_names="all", data_type="all")`

or equivalently
`datashuttle my_project upload_data --sub_names all --ses_names all --data_type all`

will transfer everything in the local project folder to the central. The convenience functions upload_all()
and download_all() can be used as shortcuts for this. See below for a full list of all sub_names, ses_names and data_type
keyword options.

A number of configuration settings define the behaviour of datashuttle during file transfer (see make_config_file). Datashuttle
uses [Rclone](https://rclone.org/) for data transfer, and these options are aliases for RClone configurations.

### overwrite_old_files

By default, datashuttle will never overwrite files in the target project folders (i.e. the
folders the data is being transferred to). This is the case even if the version of the
file in the source project folder (i.e. the folder the data is being transferred from)
is newer (as indicated by the file modification timestamp.)

When "overwrite_old_files"
this behaviour is changed, and target folder files that are older than source folder
will be overwritten.

### transfer_verbosity

When set to vv, the console and log output will become very verbose and report all defaults. When
v (default) these will report each file that is transferred and a small number of significant events.

### show_transfer_progress

When true, real-time transfer statistics will be reported and logged.

### All sub_names, ses_names and data_type keywords

For each argument, the subject, session or datatype to transfer can be specified directly, e.g.
`project.upload_data(sub_names="sub-001", ses_names=["ses-001", "ses-002]", data_type="behav" )`

However, a number of keyword arguments can be used to specify more general rules for transfer:

*sub_names*

<u> all </u>: all subjects and any non-subject files or folders at the top level (e.g. under rawdata)
will be transferred <br>

<u> all_sub </u>: all subjects, but not any non-subject files or folders at the top level will be transferred  <br>

<u> all_non_sub </u>: Only non-subject folders (or files) will be transferred from the top level <br>

*ses_names*

<u> all </u>: all sessions and any non-session or non-data-type files or folders at the subject level (e.g. within sub-001)
will be transferred <br>

<u> all_ses </u>: all sessions, but not any non-subject files or folders at the top level will be transferred. Session level
data types may still be transferred if they are specified in data_type<br>

<u> all_non_ses </u>: Only non-session (and non session-level data_type) folders (or files) will be transferred <br>


*data_type*


<u> all </u>: all data types, at the subject or session level, will be transferred, as well as non-data-type files
at the session level (e.g. within sub-001/ses-001) <br>

<u> all_data_type </u>: all data types, at the subject or session level, will be transferred. No non-data-type
files or folders at the session level will be transferred. <br>

<u> all_ses_level_non_data_type </u>: Only non-data-type files or folders at the session level will be transferred. <br>


### Filtering folders to transfer and using convenience tags

Similarly, specific subject and sessions to transfer can be selected with sub_names, ses_names and data_type
arguments. Similarly to make_sub_folders(), subject / session names must be prefixed with "sub-" or "ses-" and if this prefix
is not found, it will be added.

For example,

```
project.download_data(
sub_names=["all"],
ses_names=["ses-001", "ses-005"],
data_type="behav"
)
```

or equivalently

```
datashuttle \
my_project \
download_data \
--sub-names all
--ses-names ses-001 ses-005
--data-type behav
```

will only transfer behavioral data type folders, for sessions 1 and 5 from all subjects.

#### Convenience Tags

Similarly to make_sub_folders(), convenience tags can be used to simplfy transfers. For data transfer,
the most useful are the wildcard tag, @*@ and the @TO@ flag.

The wildcard flag can be used to avoid specifying particular parts of subject / session names that are wanted to
to tbe transferred. This is particularly useful for skipping the `date_xxxxxx` flag that might differ across sessions or subjects.

For example,
`project.upload_data(sub_names="sub-@*@", ses_names="ses-001_date-@*@", data_type="all")` or
equivalently `datashuttle my_project upload_data --sub_names sub-@*@ --ses_names ses-001_date-@*@ --data_type all`

would transfer all any first session, irregardless of date, or all subjects and all data types.

## Transferring a specific file or folder

The functions upload_project_folder_or_file() or download_project_folder_or_file() can be used to
transfer a particular, individual file or folder. The path to the file / folder, either full
or relative to the project top level folder, should be input.

## Logging

Detailed logs of all configuration changes, folder creation and data transfers are logged
to a .datashuttle folder in the local project folder. These logs are named
with the command (e.g. make_config_file), date and time of creation.

## Convenience Functions

Convenience functions can be used to quickly get relevant project information. See the API or CLI documentation
for more information.
