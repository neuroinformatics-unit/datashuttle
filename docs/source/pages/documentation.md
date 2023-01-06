# Get Started

Datashuttle is a work in progress as has not been officially released. It is not ready for use
as documented, please await first official release.

DataShuttle helps to manage and transfer a project with many "local" machines all connected to a central "remote" machine.
DataShuttle has functions to help:
* Generare BIDS-formatted directory structures
* Transfer data between remote and local machines

On first setup, it is necessary to specify the project name, paths to the local project folder (typically empty on first use, on a
local filesystem), and paths to remote project directory and the connection method.

## DataShuttle Configs

### Configuration File

To get started, import DataShuttle and initialise the class with the project name

```
from datashuttle.datashuttle import DataShuttle

project = DataShuttle("my_project")
```
The first time you use Data Shuttle, you will be prompted to make a config file containing project information.

To setup the configuration, use the "make_config_file" function.

The "local_path" argument is required to specify the top-level path to your project. This will typically be empty
on first use. e.g. if the local_path="/path/to/project", when making a new subject (e.g. sub-001) this will be
made at /path/to/project/rawdata/sub-001.

Next, the "remote_path" argument gives the path to the central remote project. This may be on a local
filesystem (e.g. if a HPC or network drive is mounted) or using SSH. on Linux systems, ~ syntax is
not supported and the full filepath must be input.

Also required is the "connection_method". This can either be "local_filesystem" or "ssh". If "ssh",
then the "remote_host_id" and "remote_host_username" options are also required (see example below).

Finally, the options "use_ephys", "use_behav"... are used to set the data types used on the local PC.
If these are not set to True, it will not be possible to make data_type directories of this type, even
if specified directly. This option is useful if there are dedicated machines for collection of
different data types.

An example call may look like:

```
project.make_config_file(
local_path="/path/to/my/project",
remote_path="/nfs/nhome/live/username/",
connection_method="ssh",
remote_host_id="ssh.swc.ucl.ac.uk",
remote_host_username="username",
use_ephys=True,
use_funcimg=True
```
or equivalently using the command-line interface

```
datashuttle \
my_project \
make_config_file \
--local-path /path/to/my/project \
--remote-path /nfs/nhome/live/username/ \
--connection-method ssh \
--remote_host_id ssh.swc.ucl.ac.uk \
--remote_host_username username \
--use_ephys --use_funcimg
```

Individual settings can be updated using update_config(), and an existing config file can be used instead using supply_config()

### setup_ssh_connection_to_remote_server()

Once configurations are set, if the "connection_method" is "ssh", the function setup_ssh_connection_to_remote_server() must be run to setup
the ssh connection to the remote server. This will allow visual confirmation of the server key, and setup a SSH key pair. This means
your password will have to be enterred only once, to setup this connection.

## Making Project Directories

Subject and session project directories can be make using the function make_sub_dir(). This function accepts a subject name (or list
of subject names), with optional session name and data type inputs. If no session or data type name is provided,
an empty subject directory will be made at the top directory level.

The full path of all created directories are logged (see "Logging" below).

e.g.
`project.make_sub_dir(sub_names="sub-001")` or equivalently `datashuttle my_project make_sub_dir --sub_names sub-001`

will make the folder tree

```
.
└── my_project/
    └── rawdata/
        └── sub-001
```

Adding a "ses_names" argument will make the specified sessions for each subject input. Similarly, for each subject / session,
all data_types will be made. The data_type argument can be a single data_type (e.g. "behav"), a list of data_types or "all",
that will make all data_types. Note that in all cases, only data_types that are flagged to use in the configs (e.g. use_behav=True)
will be made.

All subject / session names must be prefixed with "sub-" or "ses-" respectively, according to SWC-BIDS. If these prefixes
are not input, they will be automatically added. This method will also raise an error the session number already exists,
and any duplicate inputs will be removed. Finally, subject and session names must not contain spaces and should be
formatted according to SWC-BIDS.
e.g.
```
project.make_sub_dir(
sub_names=["001", "002"],
ses_names=["ses-001", "002"],
data_type=["ephys", "behav", "histology"]
```
or equivalently

```
datashuttle \
my_project \
make_sub_dir \
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

Tags can be added to easily format subject or session names. These tags include @TO@, @DATE@, @TIME@, @DATETIME.

The @TO@ tag can be used to create a range of subjects or sessions. Where the subject or session number is
usually written, a range can be created by placing boundaries on the range either side of the @TO@ tag.
e.g. using sub_names=`sub-001@TO@003_task-retinotopy` would create three subject directories:
`sub-001_task-retinotopy, sub-002_task-retinotopy` and `sub-003_task-retinotopy`.

The @DATE@, @TIME@ or @DATETIME@ flags can be used to create date, time or datetime key-value pairs in subject or session
names, depending on the current system date / time. For example:

```
project.make_sub_dir(
sub_names="sub-001@TO@002",
ses_names="ses-001_@DATE@")
```
or equivalently

```
datashuttle \
my_project \
make_sub_dir \
--sub_names sub-001@TO@002 \
--ses_names ses-001_@DATE@
```

would create the directory tree (assuming it is 01/02/2022)

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

Data transfer can be local project to remote ("upload") or remote to local project ("download"). Data
transfers are primarily managed using the upload_data() and download_data() functions.

By default, data upload or download will never overwrite files when transferring data. If an
existing file with the same name is found in the target directory, even if it is older, it will not be overwritten.
All transfer activity is printed to the console and logged (see "Logging" below), which can be used to
determine if any files were not transferred for this reason.

To transfer all data, the keyword "all" can be used for sub_names, ses_names and data_type arguments. Note that
any existing data_type will be transferred, even if the flag use_<data_type> (e.g. use_behav) is False.

> CHECK THIS <

For example, `project.upload_data(sub_names="all", ses_names="all", data_type="all")`

or equivalently
`datashuttle my_project upload_data --sub_names all --ses_names all --data_type all`

will transfer everything in the local project director to the remote. The convenience functions upload_all()
and download_all() can be used as shortcuts for this.

### Filtering directories to transfer and using convenience tags

Similarly, specific subject and sessions to transfer can be selected with sub_names, ses_names and data_type
arguments. Similarly to make_sub_dir(), subject / session names must be prefixed with "sub-" or "ses-" and if this prefix
is not found, it will be added.

For example,

```
project.download_data(
sub_names=["all"],
ses_names=["ses-001", "ses-005"],
data_type="behav"
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

Similarly to make_sub_dir(), convenience tags can be used to simplfy transfers. For data transfer,
the most useful are the wildcard tag, @*@ and the @TO@ flag.

The wildcard flag can be used to avoid specifying particular parts of subject / session names that are wanted to
to tbe transferred. This is particularly useful for skipping the `date_xxxxxx` flag that might differ across sessions or subjects.

For example,
`project.upload_data(sub_names=sub-@*@, ses_names=ses-001_date-@*@, data_type="all"` or
equivalently `datashuttle my_project upload_data --sub_names sub-@*@ --ses_names ses-001_date-@*@ --data_type all`

would transfer all any first session, irregardless of date, or all subjects and all data types.

## Transferring a specific file or folder

The functions upload_project_dir_or_file() or download_project_dir_or_file() can be used to
transfer a particular, individual file or folder. The path to the file / folder, either full
or relative to the project top level directory, should be input.

## Logging

Detailed logs of all configuration changes, directory creation and data transfers are logged
to a .datashuttle directory in the local project directory. These logs are named
with the command (e.g. make_config_file), date and time of creation.

## Convenience Functions

Convenience functions can be used to quickly get relevant project information. See the API or CLI documentation
for more information.
