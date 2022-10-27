# Data Shuttle

Datashuttle is a work in progress as has not been officially released. It is not ready for use
as documented, please await first official release.

- Convenient GUI / Python API / Command line interface Tool for project data management
- Generate standardized directory trees for projects, convenient when collecting new data
- Automatically sync data between local and remote storage after collection
- Convenient API for transfering data between local and remote hosts

## Installation

Requires anaconda install of RClone.

See [Miniconda](https://docs.conda.io/en/main/miniconda.html) for conda installation instructions. Then run:

``` 
conda install -c conda-forge rclone
```

## Setup and Usage

To get started, import DataShuttle and initialise the class with the name of your project. 

```
from datashuttle.datashuttle import DataShuttle

project = DataShuttle("my_project")
```
The first time you use Data Shuttle, you will be prompted to make a config file containing project information.
You will only need to do this once (but can change these settings at any time with ```project.update_configs()```.

See the [API documentation]((TODO) for a full list of arguments. The only required arguments are the local
folder where your project will be kept, and the path to your remote project (either local filesystem path if remote
project is as mounted drive, or SSH information (see below) if connecting with SSH.

```
project.make_config_file("C:\path\to\local\project",
                         "Z:\path\to\remote\project
```
Once the configs are setup, it is now possible to create experiment directory trees and transfer these between
local and remote filesystems.

### Make Directory Trees

The function ```project.make_sub_dir()``` can be used to flexibly create a BIDS folder tree for a subject / session. 
All subject and session folders will be automatically prefixed with "sub-" or "ses-" respetively, if not specified.

See ```project.make_config_file()``` 
or ```project.update_config``` to set which exerpiment folders (e.g. "ephys") are created.

```
project.make_sub_dir(experiment_type="all", sub_names=["001", "002", "003"], ses_names=["001", "002"])
```
Will create folder trees for three subjects, each with two sessions, for ephys, behav, histology, and imaging.                    

Mice or sessions can automatically include the date, or date and time, with the "@DATE" indicators.

e.g. 
```
project.make_sub_dir(experiment_type["ephys", "behav"], sub_names=["001"], ses_names=["001-@DATE", "002-@DATETIME"])
```
will create the below folder tree (if, for example, the date time is 1.15 pm at 02/11/22 (note the date will be read from your
system, so will be in your local (e.g. USA) format.

```
└── project_name/
    └── raw_data/
        ├── ephys/
        │   └── sub-001/
        │       ├── ses-001-02-11-22/
        │       │   └── behav/
        │       │       └── camera
        │       └── ses-002-02-11-22-1h15m/
        │           └── behav/
        │               └── camera
        └── behav/
            └── sub-001/
                ├── ses-001-02-11-22/
                └── ses-002-02-11-22-1h15m/
```

### Transfer Data

The ```project.upload_data()``` and ```project.download_data()``` can be used to transfer files between local and remote PC.

e.g.
```
project.upload_data("all", "all", "all")
```
Will copy all data from the local to remote project folder i.e. all experiment type, subject, sessions (and all files within). Files
will never be overwritten by Data Shuttle. If a file does not exist on the target system, it will be copied. If the file
already exists and has was last edited at the same time as the file been copied, there will be no change. If the file
been copied is newer than the existing file, a warning will be shown in the logs.

Specified subjects, or sessions can be easily transferred:
```
project.update_data(["behav", "imaging"], "all", ["001", "002"])
```
Will copy sessions 1 and 2 of behavioural and imaging data for all subjects from the local to remote filesystem.

```
project.download_data(["histology"], ["001", "002", "003"], ["all"])
```
Will transfer all histology sessions or subjects 1 to 3 from the remote to local project directory. 

### SSH to remote filesystem

DataShuttle supports transfering to / from remote project folder that is connected via SSH. To do, this, simply enter the SSH
details required when making the project file (see ```project.make_config_file```). To setup the connection, the 
first time running the software, run ```project.setup_ssh_connection_to_remote_server()```.

### Directory Tree

Below is an suggested folder structure based on the BIDS framework. BIDS is a data organisation format widely used in neuroimaging and human electrophysiology [[1]](https://www.nature.com/articles/s41597-019-0105-7) that has recently begun extending to animal electrophysiology [[2]](https://neurostars.org/t/towards-a-standard-organization-for-animal-electrophysiology-a-new-bids-extension-proposal/18588).

Each mouse directory is formatted as sub-XXX (e.g. sub-001) and eachs session is formatted ses-XXX (e.g. ses-001).
```
└── project_name/
    └── raw_data/
        ├── ephys/
        │   └── mouse/
        │       └── session/
        │           └── behav/
        │               └── camera
        ├── behav/
        │   └── mouse/
        │       └── session/
        └── imaging/
            └── mouse/
        │       └── session/
        └── histology/
            └── mouse/
        │       └── session/    
```                      

