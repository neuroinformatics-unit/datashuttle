# Data Shuttle

Datashuttle is a work in progressed as has not been officially released.

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

```
project.make_sub_dir(experiment_type="all", sub_names=["001", "002", "003"], ses_names=["001", "002"])
```
Will create folder trees for three subjects, each with two sessions, for ephys, behav, histology, and imaging.                    

### Directory Tree

Below is an suggested folder structure based on the BIDS framework. BIDS is a data organisation format widely used in neuroimaging and human electrophysiology [[1]](https://www.nature.com/articles/s41597-019-0105-7) that has recently begun extending to animal electrophysiology [[2]](https://neurostars.org/t/towards-a-standard-organization-for-animal-electrophysiology-a-new-bids-extension-proposal/18588).

Each mouse directory is formatted as sub-XXX (e.g. sub-001) and eachs session is formatted ses-XXX (e.g. ses-001). See ```project.make_config_file()``` 
or ```project.update_config``` to set which exerpiment folders (e.g. "ephys") are created.

Mice or sessions can automatically include the date, or date and time, with the "@DATE" indicators.

e.g. 
```
project.make_sub_dir(experiment_type["ephys", "behav"], sub_names=["001"], ses_names=["001_@DATE", "002_@DATETIME"])
```
will create the below folder tree (if, for example, the date time is 1.5 pm at 02/11/22 (note the date will be read from your
system, so will be in your local (e.g. USA) format.
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

