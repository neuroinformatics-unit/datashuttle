(make-a-new-project)=

# How to Make a New Project

This guide will cover all we need to know for setting up a new project
in **datashuttle**.

First, make sure you have
[installed and launched **datashuttle**](how-to-install).

Next, we set up **datashuttle** on a new machine we must tell it three things:

1) **project name**: The name of the project (must be the same for all
local machines tied to a project).
2) **local path**: location of the project our local machine, where we will save acquired data.
3) **central path**: location of the central data storage, where we will upload the acquired data.

```{image} /_static/datashuttle-overview.png
:alt: My Logo
:class: logo, mainlogo
:align: center
:width: 500
```
<br>

How the **central path** is set depends on whether your connection to
central storage is as a
[mounted drive](new-project-mounted-drive)
or via
[SSH](new-project-ssh).

If you are unsure of your connection method, speak to your lab administrator
or IT department.

(new-project-mounted-drive)=
## When central storage is a mounted drive

When the central storage machine is mounted as a mounted drive, we
simply need to set the **central path** as the path to
the central project as it appears on your local machine's filesystem.

:::{dropdown} Local Filesystem Example
:color: info
:icon: info

Imagine your central storage is a remote server that is mounted to
your machine at `X:\username`. You want your project folder to
be located at `X:\username\my_projects`.

In this case, you can set the **central_path** to `X:\username\my_projects`
and with **connection_method** to `local_filesystem`.

You may pass the local or central path without the **project name**,
it will be automatically included. The project folder will be located
at `X:\username\my_projects\my_project_name`.

:::

In addition, we need to tell **datashuttle** the project name and
local path where we want to put our project and hold data on
our local machine.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

From the launch page, click `Make New Project` and you will
be taken to the page where project details must be entered

```{image} /_static/screenshots/tutorial-1-make-screen-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/tutorial-1-make-screen-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

Setting up **datashuttle** is as simple as entering the `Project name`,
`Local Path` and `Central Path` into the relevant input boxes. The paths
do not need to end in the project name - this will be automatically added.

You can paste a path into the input boxes with `CTRL+V`, copy the  input path
with `CTRL+Q` or open the path in your systems filebrowser with `CTRL+O`.

Use the `Select` feature to navigate to the local and central paths
on your local filesystem.

By default, the `Connection Method` is set to `Local Filesystem`,  so
this does not need to be changed.

Once all information is input, click `Save` to set up the project.
You can then navigate to the `Project Manager` screen by clicking the
``Go To Project Screen`` that appears.
:::

:::{tab-item} Python API
:sync: python

We will first import and initialise the `DataShuttle` class with our
`project_name`.


```{code-block} python
from datashuttle import DataShuttle

project = DataShuttle("my_first_project")

```

Next, we can use the `make_config_file()` method to set up a new
project with the desired **local path**, **central path** and
**connection method**.

```{code-block} python
project.make_config_file(
    local_path="/path/to/my_projects/my_first_project",
    central_path="X:\username\my_projects\my_first_project",
    connection_method="local_filesystem",
)
```

Now the project is set up! See the later section for
[optional arguments that control data transfers](make-project-extra-arguments).

:::
::::

(new-project-ssh)=
## Connecting to central storage via SSH

Another common method of connecting to a central storage machine is via
[SSH](https://www.ssh.com/academy/ssh/protocol).

To set up SSH connection
we need to give **datashuttle** the address of the machine to connect to,
and now the **central path** will be relative to the machine
we are connecting to.

**central_host_id:** This is the address of the server you want to connect to.

**central_host_username:** This is your profile name on the server you want to
connect to.

**central path**: This is the path to the project *on the server*.

:::{dropdown} SSH Example
:color: info
:icon: info

Let's say the central project was stored on a remote server with
address `ssh.swc.ucl.ac.uk`, and your account username on the server
is `myusername`.

Finally, we want to store the project at the location (on the server)
`/ceph/my_lab/my_name/my_projects/project_name/`.

Then the input to **datashuttle** would be

**central host id**: `ssh.swc.ucl.ac.uk`

**central host username**: `myusername`

**central path**: `/ceph/my_lab/my_name/my_projects/project_name/`

You may pass the **local path** and **central path** without
the **project name**, it will be automatically included.

::::

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-create-project-ssh-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-create-project-ssh-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

THEN CLICK THROUGH SETTING UP SSH

:::
:::{tab-item} Python API
:sync: python

In Datashuttle, the
`connection_method` configuration must be set to `"ssh"`
to use the SSH protocol for data transfers.

Prior to using the SSH protocol, the host ID must be accepted and your
user account password entered. This is only required once, following this
SSH key-pairs will be used to connect via SSH. The
command `setup-ssh-connection-to-central-server` can be used to
set up an SSH connection to the *central* machine.


```{code-block} python
project.make_config_file(
	local_path="/path/to/my_projects/my_first_project",
	central_path="/central/live/username/my_projects/my_first_project",
	connection_method="ssh",
	central_host_id="ssh.swc.ucl.ac.uk",
	central_host_username="username",
)
```

Next, a one-time command to set up the SSH connection must be run:

```{code-block} python
project.setup_ssh_connection_to_central_server()
```

Running `setup-ssh-connection-to-central-server` will require verification
that the SSH server connected to is correct (pressing `y` to proceed).

Next, your password to the *central* machine will be requested.
This command sets up SSH key pairs between *local* and *central* machines.

Password-less SSH communication is set up and no further configuration should be
necessary for SSH transfer.

:::
::::

## Updating configs  [TODO: OWN HOW-TO]

Once a project has been created, the configs can be updated during at any point.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/updating-configs-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/updating-configs-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

On the `Project Manager` page, clicking the `Configs` tab will display
the current configs. Changing any config and clicking `Save` will
update the configs.

If `SSH` configs are changed, the connection to the server will need
to be reset with `Setup SSH Connection`.

:::

:::{tab-item} Python API
:sync: python

The project configs can be selectively updated with the `update_config_file()`
method. For example, to change the `local_path` and `central_path`:

```python
project.update_config_file(
    local_path="/a/new/local/path",
    central_path="/a/new/central/path"
)
```

:::
::::
To set up, we can use the `make-config-file` command to tell Datashuttle our project details.

`make-config-file` should be used when first setting up a project's configs. To update
an existing config file, use `update-config-file` with the arguments to be updated.


(make-project-extra-arguments)=
## Extra arguments (Python API)

A number of settings that control the behaviour of transfers
can be set with the `make_config_file()` method.

These configs are not relevant for the graphical interface, with the exception of
`overwrite_existing_folders` which set directly on the
Graphical Interface's `Transfer` screen.

overwrite_existing_files
: Determines whether folders and files are overwritten
during transfer. By default, Datashuttle does not overwrite any existing
folder during data transfer. <br><br>
 *e.g.* if the file `sub-001_ses-001_measure-trajectories.csv` exists on
the central project, it will never be over-written during upload
from the local to central project, even if the local version is newer. <br><br>
To change this behaviour, the configuration `overwrite_existing_files` can be set to `True`.
If **overwrite_existing_files** is `True`, files in which the  timestamp of the
target directory will be overwritten if their
timestamp is  older than the corresponding file in the source directory.

transfer_verbosity
: Set to `"vv"` for additional detail on the
transfer operation.  Set to `"v"` to only see each file that is transferred
as well as significant events that occur during transfer.


show_transfer_progress
: When `True`, real-time transfer statistics will be reported and logged.
