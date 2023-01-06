# Get Started

This is a brief introduction to getting started with DataShuttle that contains a subset of the full documentation. For more detail, please see the full documentation.

## Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle required Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.

## Initial Setup - set configurations

DataShuttle requires specification of the path to the local project directory, remote project directory and method to connect to the remote project (either "local_filesystem" or
"ssh"). It is also required to specify the data types (e.g. behav, ephys, funcimg, histology) used on the local PC. If data_type flags are not set to True, it is not possible
to create directories of these data types on the local PC.

If connection_method used is "ssh", it is necessary to also input the remote_host_id and remote_host_username configs.

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


## Making Directories

Subject and session project directories can be make using the function make_sub_dir(). This function accepts a subject name (or list
of subject names), with optional session name and data type inputs. If no session or data type name is provided,
an empty subject directory will be made at the top directory level.

All subject / session names must be prefixed with "sub-" or "ses-" respectively, according to SWC-BIDS. If these prefixes
are not input, they will be automatically added. To make a all data types, data_type="all" can be set.

Convenience tags (@TO@, @DATE@, @TIME@, @DATETIME@) for creating ranges of subjects, or automatically including
date-xxxxxx or time / datetime key-value pairs in subject or session names are also available.
An example call:

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

## Transferring Directories

Data transfer can be local project to remote ("upload") or remote to local project ("download"). Data
transfers are primarily managed using the upload_data() and download_data() functions.

By default, data upload or download will never overwrite files when transferring data. If an
existing file with the same name is found in the target directory, even if it is older, it will not be overwritten.
All transfer activity is printed to the console and logged (see "Logging" below), which can be used to
determine if any files were not transferred for this reason.

Along with the @TO@ flag, a wildcard @*@ flag can also be used in subject or session names.

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

## Logging

Detailed logs of all configuration changes, directory creation and data transfers are logged
to a .datashuttle directory in the local project directory. These logs are named
with the command (e.g. make_config_file), date and time of creation.

## Convenience Functions

Convenience functions can be used to quickly get relevant project information. See the API or CLI documentation
for more information.
