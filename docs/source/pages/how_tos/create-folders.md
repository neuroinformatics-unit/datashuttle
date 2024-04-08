(how-to-create-folders)=
# How to Create Folders

**datashuttle** creates project folders
according to the [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)
specification.

Before jumping into the folder-creation process, we'll quickly
review the key features of the
[specification](https://neuroblueprint.neuroinformatics.dev/specification.html))
that are created folders must conform to.

In [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) for each
subject and session there are datatype folders in which acquired
data is saved:

```{image} /_static/NeuroBlueprint_project_tree_dark.png
   :align: center
   :class: only-dark
   :width: 650px
```
```{image} /_static/NeuroBlueprint_project_tree_light.png
   :align: center
   :class: only-light
   :width: 650px
```
<br>


The subject and session folder names must begin with `sub-` and `ses-`
respectively—other key-value pairs are optional. All acquired data must go
in a datatype folder with a
[standard name](https://neuroblueprint.neuroinformatics.dev/specification.html).

No strong requirements are made on filenames of acquired data, but it is recommended
to include the subject and session number if possible.

Now the specification has been introduced, let's dive in to folder creation!


## Creating project folders

In the below example, folders will be created in the `rawdata` folder,
within the `my_first_project` project folder.

The project folder is located at the **local path**
specified when [setting up the project](make-a-new-project).

We will create datatype folders `behav` and `funcimg`
within a `ses-001_<todays_date>` for both `sub-001` and `sub-002`.

The below example uses the `@DATE@` convenience tag to automate
creation of today's date. See the section below for more
information on
[convenience tags](create-folders-convenience-tags).


::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui


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
<br>


Folders are created in the `Create` tab on the `Project Manager` page.

We can fill in the subject and session names and select datatype
folders to create.

Note that the `sub-` or `ses-` prefix is not actually required and will
be automatically added.

### `Create` tab shortcuts

The `Create` tab has a lot of useful shortcuts.

First, **double-clicking the subject or session input boxes** will suggest
the next subject or session to create, based on the local project.
If a [Name Template](how-to-use-name-templates) is set, the
suggested name  will also include the template.

Holding `CTRL` while clicking will add the `sub-`
or `ses-` prefix only.

Next, the **Directory Tree** has a number of useful shortcuts. These are
activated by hovering the mouse and pressing one of the below combination
of keys (you may need to click the `Directory Tree`) first:

Fill an input
: `CTRL+F` will fill the subject or session input with the name
of the folder (prefixed with `sub-` or `ses-`) that is hovered over.

Append to an input
: `CTRL+A` is similar to 'fill' above, but will instead append the name
to those already in the input. This allows creation of lists.

Open folder in system filebrowser
: `CTRL+O` will open (any) folder in the system filebrowser.

Copy the full filepath.
: `CTRL+Q` will copy the entire filepath of the file or
folder that is hovered over.


### `Create` tab Settings

Clicking the `Settings` button on the `Create` tab will give access
allow setting the top-level folder, and bypass validation.

```{image} /_static/screenshots/how-to-create-folders-settings-dark.png
   :align: center
   :class: only-dark
   :width: 500px
```
```{image} /_static/screenshots/how-to-create-folders-settings-light.png
   :align: center
   :class: only-light
   :width: 500px
```
<br>

Top-level folder
: This dropdown box will set whether folderes are created in the
`rawdata` or `derivatives` top-level folder

Bypass validation
: If on, this setting will allow folder creation even if the names
are not valid (e.g. break with
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)).

This screen is also used to set validation against
[Name Templates](how-to-use-name-templates).

:::

:::{tab-item} Python API
:sync: python

Creating folders can be done with the `create_folders()` method in the Python API.
We simply need to provide the subject, session and datatypes to create:

```python
from datashuttle import DataShuttle

project = DataShuttle("my_first_project")

created_folders = project.create_folders(
    top_level_folder="rawdata",
    sub_names=["sub-001", "002"],
    ses_names="ses-001_@DATE@",
    datatype=["behav", "funcimg"]
)
```

We provides **datashuttle** with a list of subject, session and
datatype folders to create.

Note that the `sub-` or `ses-` prefix is not actually required and will
be automatically added.

The method outputs `created_folders`, which contains a list of all
`Path`s to all created datatype folders.
:::
::::

:::{admonition} Folder Validation
:class: note

The names of the folders to be created are validated on the fly against
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/).
If the folder names will break with the specification, an error will
be raised and the folders will not be created.

Validation can be extended by defining custom templates for subject
or session names—if folders don't match the template an error will be raised.
See [How to use Name Templates](how-to-use-name-templates) for more information.

:::

(create-folders-convenience-tags)=
## Convenience Tags

There are four convenience tags that can be used in subject or session
names when creating folders. They automate the inclusion of:

Today's Date
: The `@DATE@` tag will include today's date in the format `YYYYMMDD`. \
    *e.g.* If today's date is 16th May 2024, the name `"ses-001_@DATE@"` will
create the folder `ses-001_date-20241605`.

Current Time
: The `@TIME@` tag will include the current time in the format `HHMMSS`. \
    *e.g.* If the current time is `15:10:05` (i.e. 10 minutes and 5 seconds past 3 pm.),
the name `"ses-001_@TIME@"` will create the folder `ses-001_time-151005`.

Current Datetime
: The `@DATETIME@` tag will add the
[ISO8601](https://en.wikipedia.org/wiki/ISO_8601)-formatted datetime. \
    *e.g.* If the date and time are as above, the name `"ses-001_@DATETIME@"` will
create the folder `ses-001_datetime-20241605T151005`.

A Range of Folders
: The`@TO@` tag creates a range of subject or session numbers. \
    *e.g.* `"sub-001@TO@003"` would create subject folders `sub-001`, `sub-002`, `sub-003`.
