# Documentation

DataShuttle is a tool to streamline the management and standardisation of neuroscience project folders and files.

DataShuttle's goal is to alleviate the burden researchers face in adhering to standardized file and folder specifications during the execution of intricate and demanding experimental projects. It will:

- Eliminate the need to manually integrate datasets collected across different machines (e.g. behaviour and electrophysiology acquisition machines).
- Allow convenient transfer of data between machines. This may be between a central project storage and analysis machine (e.g. ''*I want to transfer subjects 1-5, sessions 5 and 10, behavioural data only to my laptop*.'')
- Avoids re-naming and re-formatting of project folders for collaboration or dataset publication.

DataShuttle aims to integrate seamlessly into the  neuroscience data collection and analysis workflows and eliminate the need to manually , providing tools to:

- Create folder trees that adhere to SWC-Blueprint, a data management specification based on and aligned to the Brain Imaging Dataset Specification (BIDS), widely used in neuroscience.
- Convenient transfer of between machines used for data collection and analysis, and a central storage repository.

[IMAGE OF PCS]
[TODO] - make clear that \ means newline in CLI (not always clear in guides)


DataShuttle requires a one-time setup of project name and configurations.  Next, subjects, session and data-type folder trees can be conveniently created during experimental acquisition. Once acquisition is complete, data can be easily transferred from acquisition computers to a central storage machine.

### Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle additionally requires Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.


## Getting Started

Datashuttle provides a Python API and cross-platform command line interface (CLI). In this guide examples will be down using the command line, but corresponding methods can be found in the [API Reference](https://datashuttle.neuroinformatics.dev/pages/api_index.html).

The first thing to do when using DataShuttle is to setup a new project on a *local* machine.

#### *local* machines and the *central* machine

DataShuttle makes the distinction between (possibly multiple) *local* machines and a single *central* machine. DataShuttle needs to be setup once for each *local* machine, but requires no setup on the *central* machine.

A typical use case is an experiment in which behavioural data and electrophysiological data are collected on acquisition PCs. They send the data to a central server where it is stored.

Later, a subset of the data is transferred to a third machine for analysis. In this case, the behavioural and electrophysiological acquisition machine and analysis machines are 'local'. The central storage machine is the *central* machine.

### One-time project setup on a *local* machine

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

### Creating *subject* and *session* folders

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


### Data Transfer

Once a local machine is setup, created folders can be filled with acquired experimental data. Once data collection is complete, it is often required to transfer this data to a central storage machine. This is especially important if data of different types (e.g. *behaviour*, *electrophysiology*) is acquired across multiple local machines.

DataShuttle offers a convenient way of transferring entire project folders, or subsets of data. For example, the call

```
datashuttle \
my_first_project \
upload
-sub 001@TO@003
-ses 005_date-@*@ 006_date-@*@*
-dt behav
```

Will *upload* (from *local* to *central* ) behavioural sessions 5 and 6, collected at any date, for subjects 1 to 3.

The *download* command transfers data from the *central* to *local* PC. This can be useful in case you want to analyse a subset of data that is held in *central* storage.

The main data transfer commands are: `upload`, `download`, `upload-working-folder`, `download-working-folder`, `upload-entire-project`, `download-entire-project`. To understand their behaviour, it is necessary to understand the concept of the *top level folder*.

#### Understanding the 'Top Level Folder' and Transfer Methods

SWC-Blueprint defines two main *top-level folders*, `rawdata` and `derivatives`. The purpose of `rawdata` is to store data directly as acquired. The `derivatives` folder is used to store the results of processing the `rawdata`. This distinction ensures that `rawdata` is not overwritten during processing, and makes sharing of `rawdata` simpler.

```
└── my_first_project/
    ├── rawdata/
    │   └── ...
    └── derivatives/
        └── ...
```

In DataShuttle, the current working *top level folder* is by default `rawdata`. The working *top level folder* determines where folders are created (e.g. `make_sub_folders`), and from which folder data is transferred.

For example, `upload` or  `upload-working-folder` will transfer data with `rawdata` from *local* to *central*, if `rawdata` is the current *top level folder*. `upload` transfers the specified subset of folders, while `upload-working-folder` will upload the entire *top level folder*.

To change the *top level folder*, the command `set-top-level-folder` can be used. e.g.

```
datashuttle my_first_project set-top-level-folder derivatives
```

The *top level folder* setting will remain across DataShuttle sessions.

After this change, *upload* or `upload-working-folder` will transfer data in the the `derivatives` folder.

To see the current *top level folder*, the command `show-top-level-folder` can be used.

#### Transferring the entire project

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

### Summary

This concludes the *Get Started* part of the documentation. Hopefully, you are now equipped to manage an experimental project folder aligned to community standards with a few short commands. Say goodbye to the days of manual copying and pasting!

Continue reading the documentation for a full overview of DataShuttle functionalities. This includes XXX, XXX, XXX.

To discuss, contribute or give feedback on DataShuttle, please check out our discussions page and GitHub repository. Any feedback is welcomed and greatly appreciated!



## Documentation


### API Guide  [ TODO: these example commands have not been tested]

DataShuttle can be used through the command line interface (as exampled in the *Get Started* section) or through a Python API. All commands shown in the *Get Started* guide can be used similarly in the Python API (with hypens replaced by underscores).

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
	overwrite_over_files=True,
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


### Data Types

[TODO] Link to SWC-Blueprint here, no need to re-invent the wheel. Mention how `histology` is subject-level but all others are `session`. This is actually easy to re-configure by adapting a value in the source code, but it (currently) is not exposed.

### Setting up the connection to central*

#### Local Filesystem

Local filesystem transfers are typically used when the *central* machine is setup as a mounted drive. This is a common form of communication between client machines and a central server, such as a high-performance computer (HPC, also often called *clusters*).

When a *central* machine is mounted to the *Local* machine, it acts as it is available as a local-filesystem folder. In this case, the `central_path` configuration (see `make_config_file`) can simply be set to the path directing to the mounted drive.  [TODO: example]

With the `connection_method` set to `local_filesystem`, data transfer will proceed between the *local* machine filesystem and mounted drive.

#### SSH

One method of connecting with the *central* machine is the Secure Shell (SSH) protocol, that enables communication between two machines. In DataShuttle, SSH can be used as a method of communication between *local* and *central* machines.

The convenience command `setup-ssh-connection-to-central-server` can be used to setup an SSH connection to the *central* machine. The *central* machine must be a Linux-managed remote server. This command is only required to be run once.

This command requires that all configurations related to SSH communication (`central_host_id`, `central_username`) are set (using `make-config-file`). Running `setup-ssh-connection-to-central-server` will require verification that the SSH server connected to is correct (pressing `y` to proceed). Following this, your password to the *central* machine will be requested.

This command sets up SSH key pairs between *local* and *central* machines. Password-less SSH communication is setup and no further configuration should be necessary for SSH transfer.

In DataShuttle, the `connection_method` configuration must be set to `"ssh"` to use the SSH protocol for data transfers.

### Convenience tags


**Date, Time and Datetime**
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

will create the folder tree (assuming the *top level folder* is `rawdata`):

```
└── rawdata/
    └── sub-001_date-20230606/
        ├── ses-001_time-202701/
        │   └── behav
        └── ses-002_date-20230606_time-202701/
            └── behav
```


**The @TO@ flag**
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

**The wildcard flag, @\*@**
*Used when transferring data*

When transferring sessions, sessions with the same number may not always contain other days are identical. For example, consider two subjects whose test session 5 was collected on different days.

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
make_sub_folders \
-sub 001 002
-ses 005_condition-test_date-@*@
-dt behav
```

Which would selectively upload session 5 from subjects 1 and 2. Similarly, if the test session was on different session numbers for different sessions, we could use:
`-ses @*@condition-test@*@` (as the `-ses` argument above) to selectively transfer test sessions only.


#### Data Transfer


## Data Transfer Options


"all" keyword

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

### Getting Project Information

Convenience functions can be used to quickly get relevant project information. See the API or CLI documentation
for more information.

### Transferring a specific file or folder

The functions upload_project_folder_or_file() or download_project_folder_or_file() can be used to
transfer a particular, individual file or folder. The path to the file / folder, either full
or relative to the project top level folder, should be input.

### Logging

Detailed logs of all configuration changes, folder creation and data transfers are logged
to a .datashuttle folder in the local project folder. These logs are named
with the command (e.g. make_config_file), date and time of creation.
