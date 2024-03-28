(how-to-create-folders)=
# How to Create Folders

TODO: mention the walkthrough here?
TODO: add in top level folder switch and bypass validation switch

**datashuttle** automates the creation and validation of project folders
according to the [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)
specification.

Before jumping into the folder-creation process, we'll quickly
review the key features of the
[specification](https://neuroblueprint.neuroinformatics.dev/specification.html))
that are created folders must conform to.

In [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) for each
*subject* and *session* there are *datatype* folders in which acquired
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

EXPLAIN ALL SHORTCUTS!

:::

:::{tab-item} Python API
:sync: python

Creating folders can be done with the `make_folders()` method in the Python API.
We simply need to provide the subject, session and datatypes to create:

```python
from datashuttle import DataShuttle

project = DataShuttle("my_first_project")

created_folders = project.make_folders(
    sub_names=["sub-001", "002"],
    ses_names="ses-001_@DATE@",
    datatype=["behav", "funcimg"]
)
```

In this example, all folders will be created in the `rawdata` folder,
within the `my_first_project` project folder, located at the **local path**
specified when [setting up the project](make-a-new-project).

We will create subject folders `sub-001` and `sub-002`. Note that
the `sub-` or `ses-` prefix is not actually required and will
be automatically added.

Within each subject folder a session `ses-001_<todays_date>` will be created.
Datatype folders `behav` and `funcimg` will be created in the session folders.

The method outputs `created_folders`, which contains a list of all
`Path`s to all created datatype folders.

The `@DATE@` tag is a convenient method to create a session with current date
See below for more convenience tags

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
