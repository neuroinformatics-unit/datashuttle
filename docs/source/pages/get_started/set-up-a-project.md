(set-up-a-project_)=
# Set up a project

The first section of this guide will
set up a "local-only" project that can create
and validate project folders. This requires
only minimal configuration to get started.

To see how a datashuttle project can be set up for transfer,
visit the [Set up a project for transfer](set-up-a-project-for-transfer) section.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

Selecting `Make New Project` will take you to the project set up screen.

Enter the name of your project, the path to your project folder and
select `No connection (local only)` (note that the `Central Path` option
will be disabled).

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


You will now be able to go to the project manager screen:

```{image} /_static/screenshots/how-to-create-folders-example-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-create-folders-example-light.png
   :align: center
   :class: only-light
   :width: 900px
```

:::

:::{tab-item} Python API
:sync: python

First, import ``datashuttle`` and set up a project with the ``project_name``.
If a project already exists, this should match the project folder name (i.e. the level above ``rawdata``).


```python

from datashuttle import DataShuttle

project = DataShuttle("my_project_name")

```

Next, give ``datashuttle`` the path to the project folder (this can,
but doesn't have to, include the ``project_name``)

```python

project.make_config_file(
    local_path=r"C:\MyUsername\my_data\my_project_name"
)

```
\
The project is now ready for use, and in future can be instantiated
with the line ``project = DataShuttle("my_project_name")`` (i.e. you will not
have to set the `local_path` again).

If you wish to change the project settings at a later time, use ``project.update_config_file()``.

:::
::::

Now, this project is ready for creating and validating
folders to the [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) standard. See [create folders](how-to-create-folders)
and [validate folders](tutorial-validation) for details.

If you would also like to transfer files to a central storage, see the next section.

(set-up-a-project-for-transfer)=
## Set up a project for transfer

Above, we have set up a ``datashuttle`` project by providing the **project name**
and **local path**. To set up a project for transfer, we need to provide
additional information:

1) **central path**: location of the project on the central storage.
2) Connection-specific settings (e.g. if using a mounted drive, SSH, Google Drive or
Amazon Web Services (AWS)).

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
central storage is connected to through a
[mounted drive](new-project-mounted-drive), via
[SSH](new-project-ssh) or is an
[AWS S3 Bucket](new-project-aws)
or
[Google Drive](new-project-gdrive).

If you are unsure of your connection method, speak to your lab administrator
or IT department.

(new-project-mounted-drive)=
### Connecting to central storage through a mounted drive

In this case, the central storage machine is mounted as a drive
on the local machine.

We simply need to set the **central path** as the path to
the central project as it appears on the local machine's filesystem.

:::{dropdown} Local Filesystem Example
:color: info
:icon: info

Imagine your central storage is a remote server that is mounted to
your machine at `X:\username`. You want your project folder to
be located at `X:\username\my_projects`.

In this case, you can set the **central path** to `X:\username\my_projects`
and with **connection method** to **local filesystem**.

The project folder will be located
at `X:\username\my_projects\my_project_name`.
You may pass the central path without the **project name**,
(it will be automatically included).

:::

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

First, click the `Make New Project` button from the launch page.

The `Make New Project` screen will be displayed:

```{image} /_static/screenshots/tutorial-1-make-screen-local-filesystem-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/tutorial-1-make-screen-local-filesystem-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

(general-tui-datashuttle-setup)=
Setting up ``datashuttle`` is as simple as entering the `Project name`,
`Local Path` and `Central Path` into the relevant input boxes.

The paths do not need to end in the project name—it will be automatically added.
You can paste a path into the input boxes with `CTRL+V` or use `Select`
to navigate to paths on your local filesystem.

The `Connection Method` can be changed to `Local Filesystem`.

Once all information is input, click `Save` to set up the project.
You can then navigate to the `Project Manager` screen by clicking the
`Go To Project Screen` button that appears.

:::

:::{tab-item} Python API
:sync: python

We will first import the `DataShuttle` class and initialise
it with the `project_name`:


```{code-block} python
from datashuttle import DataShuttle

project = DataShuttle("my_first_project")

```

Next, the `make_config_file()` method can be used to set up a new
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
### Connecting to central storage through SSH

A common method of connecting to a central server is by using [SSH](https://www.ssh.com/academy/ssh/protocol).

The following details must be set in the project configs prior to setting up the connection:

1) **central host id:** This is the address of the server you want to connect to.

2) **central host username:** This is your profile username on the server you want to
connect to.

3) **central path**: This is the path to the project *on the server*.

Once the configs are saved, we can set up the connection by clicking `Set Up SSH Connection`
(through the TUI) or running the function [](setup_ssh_connection()) in Python.

:::{dropdown} SSH Example
:color: info
:icon: info

Let's say the central project was stored on a remote server with
address `ssh.swc.ucl.ac.uk`, and your account username on the server
is `myusername`.

We want to store the project at the location (on the server)
`/ceph/my_lab/my_name/my_projects/project_name/`.

Then the settings would be:

**central host id**: `ssh.swc.ucl.ac.uk`

**central host username**: `myusername`

**central path**: `/ceph/my_lab/my_name/my_projects/project_name/`

You may pass the **local path** and **central path** without
the **project name**, it will be automatically included.

Note that Linux-based shortcuts (e.g. `~` for home directory) are not permitted.

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

Select the `Connection Method` as `SSH`.

Next, input the `Central Host ID`, `Central Host Username` and
`Central Path` as described above.

Clicking `Save` will save these project configs. A button
`Set up SSH Connection` will appear. Click to
confirm the server ID and enter your password
(you will only need to do this once).

:::
:::{tab-item} Python API
:sync: python

The `connection_method` configuration must be set to `"ssh"`
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

Running [](setup_ssh_connection()) will require verification
that the SSH server connected to is correct (pressing `y` to proceed).

Finally, your password to the central server will be requested (you will
only need to do this once).

:::
::::

(new-project-gdrive)=
### Connecting to central storage through Google Drive

The following details control the transfer of data to [Google Drive](https://drive.google.com):

1) **gdrive root folder id:** This is the Google Drive ID of the root folder to connect to.
It is the alphanumeric code in the URL to the folder on the Google Drive website (after `/folders/`).

2) **gdrive client id** (optional): This is a client ID that can be provided to speed up data transfer.
See [here](https://rclone.org/drive/#making-your-own-client-id) for a guide on generating the client ID through
the Google API Console. If not provided, [RClone's](https://rclone.org/) shared default client ID is used, which may be slower.

3) **central path** (optional): This is the path to the project *relative to the root folder*.
If not provided, it is assumed the `gdrive_root_folder_id` points directly to the project folder.

Once the configs are saved, we can set up the connection by clicking `Set Up Google Drive Connection`
(through the TUI) or running the function [](setup_gdrive_connection()) in Python.

```{important}
If you change the `gdrive_root_folder_id`, you must re-run the connection set up.
```

:::{dropdown} Google Drive Example
:color: info
:icon: info

Let's say the central project was stored on a Google Drive folder
with root folder id `1KAN9QLD2K2EANE`, and your Google Drive client id
is `93412981629-2icf0ba09cks9skjkcrs85tinf73s2bqv.apps.googleusercontent.com`.

We want to store the project at the path (relative to the root folder)
`/my_name/my_projects/project_name/`.

Then the settings would be:

**gdrive root folder id**: `1KAN9QLD2K2EANE`

**gdrive client id**: `93412981629-2icf0ba09cks9skjkcrs85tinf73s2bqv.apps.googleusercontent.com`

**central path**: `/my_name/my_projects/project_name/`

You may pass the **central path** without
the **project name**, it will be automatically included.

::::

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-create-project-gdrive-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-create-project-gdrive-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

When setting up a new project, the **project name** and **local path**
can be input exactly the
[same as when setting with local filesystem](general-tui-datashuttle-setup).

Select the `Connection Method` as `Google Drive`.

Next, input the `Google Drive Root Folder ID`, `Client ID` and
`Central Path` as described above.

Clicking `Save` will save these project configs. A
`Set up Google Drive Connection` button will appear. Click to
start the setup, you will be required to enter your Google Drive
client secret and then authenticate via a browser.

If you do not have access to an internet browser on your machine,
instructions will be provided for browserless connection set up.

:::
:::{tab-item} Python API
:sync: python

The `connection_method` configuration must be set to `"gdrive"`
to use the Google Drive for data transfers.

Enter the `central_path`, `gdrive_root_folder_id` and
`gdrive_client_id` as  described above.

```{code-block} python
project.make_config_file(
	local_path=r"C:\path\to\local\my_projects\my_first_project",
	central_path="/my_name/my_projects/project_name/",
	connection_method="gdrive",
	gdrive_client_id="93412981629-2icf0ba09cks9skjkcrs85tinf73s2bqv.apps.googleusercontent.com",
	gdrive_root_folder_id="1KAN9QLD2K2EANE",
)
```

Next, a one-time command to set up the connection must be run:

```{code-block} python
project.setup_gdrive_connection()
```

Running [](setup_gdrive_connection()) will prompt to you to enter your
Google Drive client secret.

Finally, you will be required to authenticate to Google Drive via your browser.
If you do not have access to an internet browser on your machine,
instructions will be provided for browserless connection set up.


:::
::::

(new-project-aws)=
### Connecting to central storage through AWS S3 Bucket

The following details are required to connect to an AWS S3 Bucket:

1) **aws access key id:** This is the access key ID that allows you to connect to AWS buckets and can be set up through the AWS website.
See [here](https://repost.aws/knowledge-center/create-access-key) for a guide on creating an access key and
[this guide](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonS3FullAccess.html#AmazonS3FullAccess)
for ensuring your access key has the correct permissions. You will also require the
associated **aws secret access key** that acts as a password.

2) **aws region:** This is the region of your AWS bucket as stated on the bucket details on the AWS website.

3) **central path**:  For AWS connections, the `central_path` **must** start with the bucket name.
You can then extend this to point to the project folder on the bucket, or leave it as only the bucket
name only to transfer directly to the bucket root.

Once the configs are saved, we can set up the connection by clicking `Set Up AWS Connection`
(through the TUI) or running the function [](setup_aws_connection()) in Python.

:::{dropdown} AWS Example
:color: info
:icon: info

Let's say the central project was stored on an AWS bucket in the region
`eu-north-1`, and your AWS access key id
is `ADI82KSN29OE10CKAO92MSW9`.

We want to store the project at the path (starting with the bucket name)
`my_bucket_name/my_name/my_projects/project_name/`.

Then the settings would be:

**aws access key id**: `ADI82KSN29OE10CKAO92MSW9`

**aws region**: `eu-north-1`

**central path**: `my_bucket_name/my_name/my_projects/project_name/`

You may pass the **central path** without
the **project name**, it will be automatically included.

::::

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-create-project-aws-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-create-project-aws-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

When setting up a new project, the **project name** and **local path**
can be input exactly the
[same as when setting with local filesystem](general-tui-datashuttle-setup).

Select the `Connection Method` as `AWS S3`.

Next, input the `AWS Access Key ID`, `AWS Region` and
`Central Path` as described above.

Clicking `Save` will save these project configs. A button
`Set up AWS Connection` will appear. Click to
start the setup, you will be required to enter your `AWS Secret Access Key`.

:::
:::{tab-item} Python API
:sync: python

The `connection_method` configuration must be set to `"aws"`
to use the AWS for data transfers.

Enter the `central_path`, `aws_access_key_id` and
`aws_region` as  described above.

```{code-block} python
project.make_config_file(
	local_path=r"C:\path\to\local\my_projects\my_first_project",
	central_path="my_bucket_name/my_name/my_projects/project_name/",
	connection_method="aws",
	aws_access_key_id="ADI82KSN29OE10CKAO92MSW9",
	aws_region="eu-north-1",
)
```

Next, a one-time command to set up the AWS connection must be run:

```{code-block} python
project.setup_aws_connection()
```

Running [](setup_aws_connection()) will require entering your
`AWS Secret Access Key` and the setup will be completed.
