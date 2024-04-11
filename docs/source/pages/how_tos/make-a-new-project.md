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

```{image} /_static/datashuttle-overview-dark.png
   :align: center
   :class: only-dark
   :width: 500px
```
```{image} /_static/datashuttle-overview-light.png
   :align: center
   :class: only-light
   :width: 500px
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

(general-tui-datashuttle-setup)=
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
    local_path=r"C:\my_local_machine\username\my_projects\my_first_project",
    central_path=r"X:\a_mounted_drive\username\my_projects\my_first_project",
    connection_method="local_filesystem",
)
```

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

When setting up a new project, the **project name** and **local path**
can be input exactly the
[same as when setting without SSH](general-tui-datashuttle-setup).

Next, input the `Central Host ID`, `Central Host Username` and
`Central Path` as described above.

Clicking `Save` will save these project configs. A button
`Setup SSH Connection` will appear. Click this to
confirm the server and enter your password to the server
(you will only need to do this once)
``


:::
:::{tab-item} Python API
:sync: python

In Datashuttle, the
`connection_method` configuration must be set to `"ssh"`
to use the SSH protocol for data transfers.

Enter the `central_path`, `central_host_id` and
`central_host_username` as  described above.

```{code-block} python
project.make_config_file(
	local_path=r"C:\path\to\local\my_projects\my_first_project",
	central_path="/nfs/path_on_server/myprojects/central",
	connection_method="ssh",
	central_host_id="ssh.swc.ucl.ac.uk",
	central_host_username="username",
)
```

Next, a one-time command to set up the SSH connection must be run:

```{code-block} python
project.setup_ssh_connection()
```

Running `setup_ssh_connection()` will require verification
that the SSH server connected to is correct (pressing `y` to proceed).

Finally, your password to the central server will be requested (you will
only need to do this once).

:::
::::
