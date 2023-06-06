# Full Documentation

Datashuttle is a work in progress as has not been officially released. It is not ready for use
as documented, please await first official release.

DataShuttle helps to manage and transfer a project with many "local" machines all connected to a "central" machine.
DataShuttle has functions to help:
* Generate BIDS-formatted folder structures
* Transfer data between central and local machines

On first setup, it is necessary to specify the project name, paths to the local project folder (typically empty on first use, on a
local filesystem), and paths to central project folder and the connection method.

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

Finally, the settings "overwrite_old_files_on_transfer", "transfer_verbosity" and "show_transfer_progress" determine
the behaviour during file transfer. Please see the Data Transfer section for more information.

An example call may look like:

```
project.make_config_file(
local_path="/path/to/my/my_project",
central_path="/nfs/nhome/live/username/",
connection_method="ssh",
central_host_id="ssh.swc.ucl.ac.uk",
central_host_username="username",
overwrite_old_files_on_transfer=True,
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
--use-ephys --use-behav --use-histology --overwrite_old_files_on_transfer
```

Individual settings can be updated using update_config(), and an existing config file can be used instead using supply_config()

### Setting up an SSH Connection

Once configurations are set, if the "connection_method" is "ssh", the function setup_ssh_connection_to_central_server() must be run to setup
the ssh connection to the central server. This will allow visual confirmation of the server key, and setup a SSH key pair. This means
your password will have to be enterred only once, when setting up this connection.

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
transfers are primarily managed using the upload() and download() functions.

By default, uploading or downloading data will never overwrite files when transferring data. If an
existing file with the same name is found in the target folder, even if it is older, it will not be overwritten.
All transfer activity is printed to the console and logged (see "Logging" below), which can be used to
determine if any files were not transferred for this reason.

To transfer all data, the keyword "all" can be used for sub_names, ses_names and data_type arguments. Note that
any existing data_type will be transferred, even if the flag use_<data_type> (e.g. use_behav) is False.

For example, `project.upload(sub_names="all", ses_names="all", data_type="all")`

or equivalently
`datashuttle my_project upload --sub_names all --ses_names all --data_type all`

will transfer everything in the local project folder to the central. The convenience functions upload_working_folder()
and download_working_folder() can be used as shortcuts for this. See below for a full list of all sub_names, ses_names and data_type
keyword options.

A number of configuration settings define the behaviour of datashuttle during file transfer (see make_config_file). Datashuttle
uses [Rclone](https://rclone.org/) for data transfer, and these options are aliases for RClone configurations.

### overwrite_old_files_on_transfer

By default, datashuttle will never overwrite files in the target project folders (i.e. the
folders the data is being transferred to). This is the case even if the version of the
file in the source project folder (i.e. the folder the data is being transferred from)
is newer (as indicated by the file modification timestamp.)

When "overwrite_old_files_on_transfer"
this behaviour is changed, and target folder files that are older than source folder
will be overwritten.

### transfer_verbosity

When set to vv, the console and log output will become very verbose and report all defaults. When
v (default) these will report each file that is transferred and a small number of significant events.

### show_transfer_progress

When true, real-time transfer statistics will be reported and logged.

### All sub_names, ses_names and data_type keywords

For each argument, the subject, session or datatype to transfer can be specified directly, e.g.
`project.upload(sub_names="sub-001", ses_names=["ses-001", "ses-002]", data_type="behav" )`

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
project.download(
sub_names=["all"],
ses_names=["ses-001", "ses-005"],
data_type="behav"
)
```

or equivalently

```
datashuttle \
my_project \
download \
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
`project.upload(sub_names="sub-@*@", ses_names="ses-001_date-@*@", data_type="all")` or
equivalently `datashuttle my_project upload --sub_names sub-@*@ --ses_names ses-001_date-@*@ --data_type all`

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
