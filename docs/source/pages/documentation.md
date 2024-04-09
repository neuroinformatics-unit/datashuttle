:tocdepth: 2

# User Guide

Datashuttle is a tool to help standardise neuroscience project folders.

Datashuttle's goal is to alleviate the burden of maintaining
sharable experimental project folders by:

- Automating the creation of standardised project folders.
- Allowing convenient transfer of data between machines.
- Eliminating the requirement to manually combine data collected across
different acquisition machines.

Datashuttle aims to integrate seamlessly into existing neuroscience data
collection and analysis workflows.

## Datashuttle's place in neuroscience pipelines

A typical setup in systems neuroscience is that multiple acquisition
machines collect experimental data (e.g. separate machines for acquiring
behaviour and electrophysiology).

The data from these separate machines are then combined
in a central storage machine - this may be a particular computer
in the lab or a high-performance computing (HPC) system.

Following data collection, the entire project or subsets of the data are downloaded
to other machines (e.g. a researcher's laptop) for analysis.

<img src="https://github.com/neuroinformatics-unit/datashuttle/assets/29216006/51b65a6d-492a-4047-ae7b-16273b58e258" alt="datashuttle central and local machines" class="img-responsive"/>

Datashuttle facilitates the creation of standardised project folders and data transfer between
acquisition, central storage and analysis machines.

Datashuttle manages datasets that are formatted according to the
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) specification.

::: {dropdown} Data specifications for neuroscience
:color: info
:icon: info

A data specification details the folder structure and naming scheme for a project.
The most widely used specification for data-sharing in neuroscience is the [BIDS](https://bids.neuroimaging.io/) specification.
First developed  for human imaging, it has since been extended to other methodologies used in
human experimental neuroscience (e.g. EEG, MEG) .

Extensions to systems neuroscience datatypes are currently in progress
(e.g. [microscopy](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/10-microscopy.html),
[electrophysiology BEP](https://bep032tools.readthedocs.io/en/latest/)).

While BIDS is an excellent, extensive formal specification, the detailed requirements necessary for data-sharing
are difficult to maintain during data-acquisition. It is also yet to be fully extended to
systems neuroscience.

Therefore, we have introduced [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/),
a lightweight specification heavily inspired by BIDS for use during data acquisition. Organising
data according to [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) during acquisition
will facilitate conversion to full BIDS for data sharing if required.

:::
<br>

# Installation


We recommend you install Datashuttle inside a [conda](https://docs.conda.io/en/latest/)
or [mamba](https://mamba.readthedocs.io/en/latest/index.html) environment.

In the following we assume you have `conda` installed,
but the same commands will also work with `mamba`/`micromamba`.

First, create and activate an environment.
You can call your environment whatever you like, we've used "datashuttle-env".

```sh
conda create -n datashuttle-env -c conda-forge python=3.10 rclone
conda activate datashuttle-env
```

Next install the `datashuttle` package:

::::{tab-set}

:::{tab-item} Users
To get the latest release from PyPI:

```sh
pip install datashuttle
```
If you have an older version of `datashuttle` installed in the same environment,
you can update to the latest version with:

```sh
pip install --upgrade datashuttle
```
:::

:::{tab-item} Developers
To get the latest development version, clone the
[GitHub repository](https://github.com/neuroinformatics-unit/datashuttle/)
and then run from inside the repository:

```sh
pip install -e .[dev]  # works on most shells
pip install -e '.[dev]'  # works on zsh (the default shell on macOS)
```

This will install the package in editable mode, including all `dev` dependencies.
:::

::::


# Setup

The first thing to do when starting with Datashuttle is to setup a new project on a *local* machine.

First, we need to tell Datashuttle the path to the project folder on our *local* machine
and how we want to connect to the *central* storage machine.


## *local* machines and the *central* machine

Datashuttle makes the distinction between  *local* machines and a single *central* machine.
There may be multiple *local* machines, but only one *central* machine.

*local* machines are typically acquisition and analysis machines, whereas the
*central* machine is used for data storage.

Datashuttle needs to be setup once for each *local* machine, but requires no
setup on the *central* machine.

::: {dropdown} Example: Datashuttle use in a neuroscience project
:color: info
:icon: info

Imagine an experiment in which two different types of data, behavioural and
electrophysiological, are collected on separate acquisition PCs.
These data are sent to a central server where they are combined
and stored.

Later, a subset of the data is transferred to a third machine for analysis. It is
usually necessary to only download  a subset of the data for particular analyses
(e.g. "I want to transfer subjects 1-5, sessions 5, behavioural data
to my laptop".)

In this case, the behavioural and electrophysiological acquisition machine and
analysis machines are *local*; the central storage machine is the *central* machine.

:::

## Setting up Datashuttle

A one-time setup on each *local* machine used is required, specifying the
`project_name` and configs (short for 'configurations').

To interact with Datashuttle, a cross-platform command line interface (CLI)
and a Python API are available (see [API](API_Reference) and [CLI](CLI_Reference)
for reference documentation).

To set up, we can use the `make-config-file` command to tell Datashuttle our project details.

::: {dropdown} Updating an existing configuration file.
:color: info
:icon: info

`make-config-file` should be used when first setting up a project's configs. To update
an existing config file, use `update-config-file` with the arguments to be updated.

Using `make-config-file` will completely overwrite any existing configurations, including
setting any optional arguments that are not passed to factory default values.

:::

We need to tell Datashuttle:

- The paths to the *local* and *central* folders that contain the project.
- How to connect to the *central* machine.
- The settings that specify how data is transferred.
- The *[datatypes](#datatype-folders)* that will be used in the project, e.g. behaviour (`behav`) or electrophysiology (`ephys`).

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
from datashuttle import DataShuttle

project = DataShuttle("my_first_project")

project.make_config_file(
	local_path="/path/to/my_projects/my_first_project",
	central_path="/central/live/username/my_projects/my_first_project",
	connection_method="local_filesystem",
)
```
:::

:::{tab-item} CLI (macOS / Linux)

macOS and Linux, ``\`` allows the command to continue on a new line.

```{code-block} console
datashuttle \
my_first_project \
make-config-file \
/path/to/my_projects/my_first_project \
/central/live/username/my_projects/my_first_project \
local_filesystem
```
:::

:::{tab-item} CLI (Windows)

On Windows, the `^` character allows the command to continue on a new line.

```{code-block} console
datashuttle ^
my_first_project ^
make-config-file ^
C:\path\to\my_projects\my_first_project ^
/central/live/username/my_projects/my_first_project ^
local_filesystem
```
:::

::::

### Required Arguments

**local_path**: The full file path to the project folder on the *local* machine,
including the project folder. The project folder must have the same name as the
Datashuttle project. For example, if your project name is `my_first_project`,
and the project folder resides in `C:\User\my_projects`, the `local_path`
should be `C:\User\my_projects\my_first_project`.

**central_path**: The path on the *central* machine to the project folder. Similar to the
`local_path`, the path must point to the project folder that has the same name as
the project in Datashuttle. For example, if your project is called `my_first_project`,
connecting to a remote Linux server, the `central_path` may be
`/hpc/home/user/my_projects/my_first_project`.

**connection_method**: `local_filesystem` or `ssh`. Local filesystem can be used
if the *central* storage is mounted to the local machine. Otherwise `ssh` can be used.
See [setting up the connection to central](#setting-up-the-connection-to-central) for
more information.


### Optional Arguments

If connection method is `ssh`, the **central_host_id** and **central_host_username**
must be set. See the [SSH section](#ssh) for details.

The optional arguments **overwrite_existing_files**, **transfer_verbosity** and
**show_transfer_progress** determine how data transfer is performed
(see the [Data Transfer](#data-transfer) section for details).

Custom config files can be supplied using the `supply-config`
command (this simplifies setting up projects across multiple *local* machines).


## Setting up the connection to *central*

### Local Filesystem

Local filesystem transfers allow transfer of files and folders across the
file system available to the machine. This is used when the *central* machine is
setup as a mounted drive. This is a common form of communication between
client machines and a server, such as a high-performance computer
(HPC, also often called a *cluster*).

When a *central* machine is mounted to the *local* machine, the folders of the
*central* machine are available as if they were part of the *local* filesystem.
In this case, the `central_path` configuration (see `make-config-file`)
can simply be set to the path directed to the mounted drive.

With the `connection_method` set to `local_filesystem`, data transfer will
proceed between the *local* machine filesystem and mounted drive.

::: {dropdown} Local Filesystem Example
:color: info
:icon: info

Imagine your *central* data store is a HPC cluster. Your projects are stored in your
home drive, with the project folder at `/system/home/username/my_projects/my_first_project`.

You have mounted your home drive, `/system/home/username` to your local filesystem,
at the path `X:\username`.

In this case, you can set the `central_path` to `X:\username\my_projects\my_first_project`
and set `connection_method` to `local_filesystem` to transfer data from
*local* to *central*.

:::

### SSH

An alternative method of connecting to the *central* machine is the Secure Shell (SSH).
To use the SSH connection protocol, additional configs must be provided that
tell Datashuttle how to connect.

**central_host_id:** This is the address of the server you want to connect to.

**central_host_username:** This is your profile name on the server you want to
connect to.


In Datashuttle, the
`connection_method` configuration must be set to `"ssh"`
to use the SSH protocol for data transfers.

Prior to using the SSH protocol, the host ID must be accepted and your
user account password entered. This is only required once, following this
SSH key-pairs will be used to connect via SSH. The
command `setup-ssh-connection-to-central-server` can be used to
setup an SSH connection to the *central* machine.

:::::{dropdown} SSH Example
:color: info
:icon: info

When setting up a project for SSH connection, the `central_host_id`
and `central_host_username` must be provided:


::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.make_config_file(
	local_path="/path/to/my_projects/my_first_project",
	central_path="/central/live/username/my_projects/my_first_project",
	connection_method="ssh",
	central_host_id="ssh.swc.ucl.ac.uk",
	central_host_username="username",
)
```
:::

:::{tab-item} CLI (macOS / Linux)

```{code-block} console
datashuttle \
my_first_project \
make-config-file \
/path/to/my_projects/my_first_project \
/central/live/username/my_projects/my_first_project \
ssh \
--central_host_id ssh.swc.ucl.ac.uk \
--central_host_username username
```
:::

:::{tab-item} CLI (Windows)

```{code-block} console
datashuttle ^
my_first_project ^
make-config-file ^
C:\path\to\my_projects\my_first_project ^
/central/live/username/my_projects/my_first_project ^
ssh ^
--central_host_id ssh.swc.ucl.ac.uk ^
--central_host_username username
```
:::

::::

Next, a one-time command to setup the SSH connection must be run:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.setup_ssh_connection()
```
:::

:::{tab-item} CLI (macOS / Linux / Windows)
```{code-block}
datashuttle my_new_project setup-ssh-connection-to-central-server
```
:::

::::

Running `setup-ssh-connection-to-central-server` will require verification
that the SSH server connected to is correct (pressing `y` to proceed).

Next, your password to the *central* machine will be requested.
This command sets up SSH key pairs between *local* and *central* machines.

Password-less SSH communication is setup and no further configuration should be
necessary for SSH transfer.

:::::

Next, we can start setting up the project by automatically creating standardised
project folder trees.

# Data Transfer

Datashuttle offers a convenient way of transferring entire project folders or
subsets of the data.

The main data transfer commands are: `upload`, `download`, `upload-all`,
`download-all`, `upload-entire-project`, `download-entire-project`. The term *upload* refers to transfer from
*local* to the *remote* machine, while *download* transfers in the opposite direction.

These commands act differently in regard to the *top-level-folder*. In Datashuttle, the current working
*top-level-folder* is by default *rawdata*. The working *top-level-folder* determines  where folders
are created (e.g. `create_folders`) and how commands transfer data.


:::{dropdown} *top-level-folders*
:color: info
:icon: info

The top-level-folders are the folders immediately under the
project root (i.e. the folders within the folder that has the name of the project).

[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) defines two main *top-level-folders*, *rawdata* and *derivatives*.
The purpose of *rawdata* is to store data directly as acquired.
The *derivatives* folder is used to store the results of processing the *rawdata*.
This distinction ensures that *rawdata* is not overwritten during processing, and
makes sharing of *rawdata* simpler.

```
└── my_first_project/
    ├── rawdata/
    │   └── ...
    └── derivatives/
        └── ...
```

To change the *top-level-folder*, the command `set-top-level-folder` can be used. e.g.

```{code-block} console
datashuttle my_first_project set-top-level-folder derivatives
```

The *top-level-folder* setting will remain across Datashuttle sessions.

To see the current *top-level-folder*, the command `get-top-level-folder` can be used.

:::


To quickly transfer the entire project (i.e. everything in all _top-level-folders_),  `upload-entire-project` and `download-entire-project` can be used.

For example, the command:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.upload_entire_project()
```
:::

:::{tab-item} CLI (macOS / Linux / Windows)
`datashuttle my_first_project upload-entire-project`
:::

::::

when run on the folder tree:

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

will transfer all files and folders in both the *rawdata* and *derivatives* folders from the
*local* machine to the *central* machine.

In contrast, `upload-all` and `download-all` will transfer the entire *top-level-folder*.
For example, if *rawdata* is the current *top-level-folder*, `upload-all` will transfer all contents of
*rawdata* from *local* to *central*.


## Selective transfer of data with `upload` and `download`

Subsets of *subjects*, *sessions* and *datatypes* can be transferred with
the `upload` and `download` commands.

For example, the call:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.upload(
	sub_names="001@TO@003",
	ses_names=["005_date-@*@", "006_date-@*@"],
	datatype="behav"
)
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub 001@TO@003 \
-ses 005_date-@*@ 006_date-@*@* \
-dt behav
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub 001@TO@003 ^
-ses 005_date-@*@ 006_date-@*@* ^
-dt behav
```
:::

::::
will *upload*
behavioural sessions 5 and 6, collected on any date, for subjects 1 to 3.

The keyword `all` can be input in place of a `-sub`, `-ses` or _datatype_
argument `-dt` to transfer all available subject, sessions or datatypes available.

Often additional files or folders may be stored outside of *datatype*
folders. The `all` argument will transfer all files and folders at the
specified level. Datashuttle offers a flexible argument syntax for
selecting precise data subsets, see [Data Transfer Options](#data-transfer-options)
for details.

## Transferring a specific file or folder

The functions `upload-specific-folder-or-file` or `download-specific-folder-or-file`
can be used to transfer an individual file or folder.

The path to the file or folder (either full or relative to the working *top-level-folder*)
should be input.


# Advanced Usage

## Convenience tags

Datashuttle provides convenience tags that can be included in
*subject* or *session* names during folder creation or transfer. These
tags help automate repetitive routines and add flexibility to
data transfers.

### Automatically include *date*, *time* or *datetime*
*Used when making subject or session folders*

When creating subject or session folders, it is often desirable to include the
*date*, *time*, or *datetime* as a key-value pair in the folder name. For example:

`ses-001_date-20230516`

Datashuttle provides convenience tags to automatically format a key-value pair
with the current date or time (as determined from the machine *datetime*).

For example, the command:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.create_folders(
    top_level_folder="rawdata",
	sub_names="sub-001",
	ses_names=["001_@DATETIME@", "002_@DATETIME@"],
	datatype="behav",
)
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
create_folders \
-sub sub-001 \
-ses 001_@DATETIME@ 002_@DATETIME@ \
-dt behav
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
create_folders ^
-sub sub-001 ^
-ses 001_@DATETIME@ 002_@DATETIME@ ^
-dt behav
```
:::

::::

creates the folder tree (assuming the *top-level-folder* is _rawdata_):

```
└── rawdata/
    └── sub-001/
        ├── ses-001_datetime-20230606T202701/
        │   └── behav
        └── ses-002_datetime-20230606T202701/
            └── behav
```


### Specify ranges with the `@TO@` flag
*When making subject or session folders and transferring data*

Often it is desirable to specify a range of subject or session names for
folder creation or data transfer.

For example, in a project with 50 subjects (`sub-001`, `sub-002`, `...`, `sub-050`),
the below command transfers only the first 25 subjects:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.upload(
	sub_names="001@TO@025",
	ses_names="all",
	datatype="all",
)
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub 001@TO@025 \
-ses all \
-dt all
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub 001@TO@025 ^
-ses all ^
-dt all
```
:::

::::

When making folders with the `@TO@` tag, the maximum number of leading zeros
found either side of the tag will be used for folder creation. For example,
setting `-sub` to `0001@TO@02` will create the subject folders `sub-0001` and `sub-0002`.

### The wildcard flag `@*@`
*Used when transferring data*

When selected subjects and sessions for data transfer, it is often
necessary to match only part of the folder name. In this case, wildcards
can be included in the search term.

For example, we may want to transfer the 5th session for all subjects
in the project folder below:

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

We can use the wildcard tag in the *session* name to match
everything that comes after the `date` key:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.upload(
	sub_names=["001", "002"],
	ses_names="005_condition-test_date-@*@",
	datatype="behav",
)
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub 001 002 \
-ses 005_condition-test_date-@*@ \
-dt behav
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub 001 002 ^
-ses 005_condition-test_date-@*@ ^
-dt behav
```
:::

::::

This command would transfer session 5 from subject 001 and 002.

::: {warning}

If using the z-shell (zsh) - which is the default shell on macOS -
text including the `@*@` tag must be wrapped in quotation marks.
e.g. `--ses "005_condition-test_date-@*@"`)
:::

## Data Transfer Options

A number of [Rclone](https://rclone.org/) options are exposed in Datashuttle to facilitate flexible data transfer.

### Overwriting existing files

`overwrite_existing_files` determines whether folders and files are overwritten
during transfer. By default, Datashuttle does not overwrite any existing
folder during data transfer.

For example, if the file `sub-001_ses-001_measure-trajectories.csv` exists on
the *central* repository, it will never be over-written during upload
from *local* to *central*, even if the version on *local* is newer.

To change this behaviour, the configuration `overwrite_existing_files` can be set to `True`.
In this case, files in which the  timestamp of the target directory (e.g. *central*
in our example) will be overwritten if their timestamp is
older than the corresponding file in the source directory.

The configuration can be changed with the `update-config-file` command.

### Additional Transfer Configurations

`transfer_verbosity` : set to `"vv"` for additional detail on the transfer operation.
Set to `"v"` to only see each file that is transferred as well as significant events that occur during transfer.

`show_transfer_progress` : When `True`, real-time transfer statistics will be reported and logged.

### Flexible transfers with keyword arguments

Often additional files or folders may be stored outside *datatype*
folders. The `all` argument will transfer all files and folders at the
specified level.

For example, consider the project below. This project has files
stored within *datatype* folders, but additional files outside *datatype*
folders at the *subject* and *session* levels.
```
.
└── rawdata/
    ├── a_project_related_file.json
    ├── sub-001/
    │   ├── sub-001_extra-file.json
    │   └── ses-001/
    │       ├── ses-001_extra-file.json
    │       ├── behav/
    │       │   └── ...
    │       └── ephys/
    │           └── ...
    └── sub-002/
        ├── sub-002_extra-file.json
        └── ses-001/
            ├── behav/
            │   └── ...
            ├── ephys/
            │   └── ...
            └── anat/
                └── ...
```

Datashuttle provides a number of keyword arguments to allow separate
handling of files that are not found in *datatype* folders.

These are:
`all_sub` and `all_non_sub` (for `-sub`), `all_ses` and `all_non_ses` (for `-ses`) and `all_non_datatype` (for `-dt`).


#### For use with the `-sub` / `--sub-names` flag

`all` - All *subject* and non-*subject* files and folders within the *top-level-folder*
(e.g. _rawdata_) will be transferred.

`all_sub` - *Subject*  <u>folders</u> only (i.e. prefixed with `sub`) and everything
within them will be transferred.

`all_non_sub` - All files and folders that are not prefixed with `sub`,
within the *top-level-folder*, will be transferred.
Any folders prefixed with `sub` at this level will not be transferred.

#### For use with the `-ses` / `--ses-names` flag

`all` : All *session* and non-*session* files and folders within a *subject* level folder
(e.g. `sub-001`) will be transferred.

`all_ses` : *Session* <u>folders</u> only (i.e. prefixed with `ses`) and everything within
them will be transferred.

`all_non_ses` : All files and folders that are not prefixed with `ses`, within a *subject* folder,
will be transferred. Any folders prefixed with `ses` will not be transferred.

#### For use with the `-dt` / `--datatype` flag

`all` : All *datatype* folders at the *subject* or *session* folder level will be transferred,
as well as all files and folders within selected *session* folders.

`all_datatype` : All *datatype* folders (i.e. folders with the pre-determined name:
`behav`, `ephys`, `funcimg`, `anat`) within a *session* folder will be
transferred. Non-*datatype* folders at the *session* level will not be transferred

`all_non_datatype` : Non-*datatype* folders within *session* folders only will be transferred

Below, a number of examples are given to exemplify how these arguments effect data transfer.
Given our example *local* project folder above:

1) The first example indicates the effect of selectively transferring non-*datatype* sessions.

2) The command:

::::{tab-set}

:::{tab-item} Python API
```{code-block} console
project.upload("all", "all", "all_non_datatype")
```
:::


:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub all \
-ses all \
-dt all_non_datatype
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub all ^
-ses all ^
-dt all_non_datatype
```
:::

::::


Would upload:

- All non-*subject* files in the *top-level* folder (i.e. `a_project_related_file.json`.)
- The `sub-001_extra_file.json` and `sub-002_extra_file.json`
- For `sub-001`, the file `ses-001_extra_file.json`.
For `sub-002`, no other files are transferred because there is no non-*datatype* files at the *session* level.


2) The next two examples show the effect of selecting `-dt all` vs. `-dt all_datatype`. The command:

::::{tab-set}

:::{tab-item} Python API
```{code-block} console
project.upload("sub-001", "all", "all")
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub 001 \
-ses all \
-dt all
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub 001 ^
-ses all ^
-dt all
```
:::

::::

Would upload:

- Contents residing in the `sub-001` folder only.
-  The file `sub-001_extra-file.json` and *session* folders.
- All *datatype* folder contents (`behav`, `ephys`) and non-*datatype* files (`ses-001_extra-file.json`).

The command:

::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.create_folders(
    top_level_folder="rawdata",
	sub_names="001",
	ses_names="all",
	datatype="all_datatype"
)
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub 001 \
-ses all \
-dt all_datatype
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub 001 ^
-ses all ^
-dt all_datatype
```
:::

::::


Would upload:

- Contents residing in the `sub-001` folder only.
- The *session* folder and all *datatype* folder contents (`behav`, `ephys`)
but not the non-*datatype* file `ses-001_extra-file.json`.

3) The final example shows the effect of transferring `all_non_sub` files only. The command:


::::{tab-set}

:::{tab-item} Python API
```{code-block} python
project.create_folders(
    top_level_folder="rawdata",
	sub_names="all_non_sub",
	ses_names="all",
	datatype="all"
)
```
:::

:::{tab-item} CLI (macOS / Linux)
```{code-block} console
datashuttle \
my_first_project \
upload \
-sub all_non_sub \
-ses all \
-dt all
```
:::

:::{tab-item} CLI (Windows)
```{code-block} console
datashuttle ^
my_first_project ^
upload ^
-sub all_non_sub ^
-ses all ^
-dt all
```
:::

::::

Would upload:

- the file `a_project_related_file.json` only.

## Query Datashuttle for current settings

A number of commands exist to query Datashuttle's current configs.
For example the `show-local-path` command will print the currently set *local* path to the terminal.
The command `show-configs` will print all currently set configs.

For a full list of available commands, see the [API reference](API_Reference) or [CLI reference](CLI_Reference).


## Logging

Detailed logs of all configuration changes, folder creation and data transfers are stored
to the `.datashuttle` folder that is created in the *local* project folder.

The log itself contains relevant information pertaining to that command.
For example, if the commands `create_folders`, `upload`, `download` were run sequentially,
the logs output folder would look like:

```
20230608T095514_create-folders.log
20230608T095545_upload-data.log
20230608T095621_download-data.log
```
