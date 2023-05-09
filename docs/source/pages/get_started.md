# Get Started

This is a brief introduction to getting started with DataShuttle, containing a subset of the full documentation.
For more detail, please see the full documentation.

This documentation gives examples both using the API (in the python console) or using the command line interface (in system terminal).

## Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle required Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.

## Initial Setup - Set Configurations

To get started, import DataShuttle and initialise the class with the project name. If using the command
line this step is not necessary.

```
from datashuttle.datashuttle import DataShuttle

project = DataShuttle("my_project")
```

DataShuttle helps to manage and transfer a project with many "local" machines all connected to a central "remote" machine.
DataShuttle requires a path to the local project folder (this is typically empty on first use and should include the name of the project
e.g. local_path="/path/to/my_project"). Also, remote project folder and method to connect to the remote project (either "local_filesystem" or
"ssh").

It is also required to specify the data types (e.g. behav, ephys, funcimg, histology) used on the local PC. If data_type flags are not set to True, it will not be possible
to create folders of these data types.

If connection_method used is "ssh", it is necessary to also input the remote_host_id and remote_host_username configs.

The settings "overwrite_old_files_on_transfer", "transfer_verbosity" and "show_transfer_progress" determine
the behaviour during file transfer. Please see the Data Transfer section of the full documentation for more information.


An example call:

```
project.make_config_file(
local_path="/path/to/my/my_project",
remote_path="/nfs/nhome/live/username/",
connection_method="ssh",
remote_host_id="ssh.swc.ucl.ac.uk",
remote_host_username="username",
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
--remote_host_id ssh.swc.ucl.ac.uk \
--remote_host_username username \
--transfer_verbosity v \
--use-ephys --use-behav --use-histology --overwrite_old_files_on_transfer
```

Individual settings can be updated using update_config(), and an existing config file can be used instead using supply_config()

### Setting up an SSH Connection

Once configurations are set, if the "connection_method" is "ssh", the function setup_ssh_connection_to_remote_server() must be run to setup
the ssh connection to the remote server. This will allow visual confirmation of the server key, and setup a SSH key pair. This means
your password will have to be enterred only once, when setting up this connection.


## Making Folders

Subject and session project folders can be made using the function make_sub_folders(). This function accepts a subject name (or list
of subject names), with optional session name and data type inputs. If no session or data type name is provided,
an empty subject folder will be made at the top folder level.

All subject or session names must be prefixed with "sub-" or "ses-" respectively, as according to SWC-BIDS. If these prefixes
are not input, they will be automatically added. To make all data types (i.e. all datatypes for which use_<data_type> configuration is true),
 data_type="all" can be set.

Convenience tags (@TO@, @DATE@, @TIME@, @DATETIME@) for creating ranges of subjects, or automatically including
date-xxxxxx or time / datetime key-value pairs in subject or session names are also available.

An example call:

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

## Data Transfer

Data transfer can be either from the local project to the remote project ("upload") or from the remote to local project("download"). Data
transfers are primarily managed using the upload_data() and download_data() functions.

By default, uploading or downloading data will never overwrite files when transferring data. If an
existing file with the same name is found in the target folder, even if it is older, it will not be overwritten.
All transfer activity is printed to the console and logged (see "Logging" below), which can be used to
determine if any files were not transferred for this reason.

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

will only transfer behavioral data type folders, for sessions 1 and 5 from all subjects. See the "All sub_names, ses_names and data_type keywords"
section of the full documentation for more options.

Along with the @TO@ flag, a wildcard @*@ flag can also be used in subject or session names.

The settings "overwrite_old_files_on_transfer", "transfer_verbosity" and "show_transfer_progress" determine
the behaviour during file transfer. Please see the Data Transfer section of the full documentation for more information.

## Logging

Detailed logs of all configuration changes, full paths to created folders and data transfers are logged
to a .datashuttle folder in the local project folder. These logs are named
with the command (e.g. make_config_file), date and time of creation.

## Convenience Functions

Convenience functions can be used to quickly get relevant project information. See the API or CLI documentation
for more information.
