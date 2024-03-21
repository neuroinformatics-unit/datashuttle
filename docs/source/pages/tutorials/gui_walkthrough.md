(gui_walkthrough)=
# Graphical Walkthrough

1) go thrugh with a fine tooth comb - make things extremely simple
2) Partition into shared vs. TUI parts
3) Possibly re-write non-tui parts with the existing python API docs
4) add tui images
5) TODO: add estimated time to complete


## Introduction

The purpose of this walk-through is to give a full introduction to setting
up and running a new neuroscience project with **datashuttle**.

By the end of the project, we will have created a 'mock' project,
standardised to the [NeuroBlueprint](neuroblueprint.neuroinformatics.dev) style

[!!TODO: should use from filetree?!!]
```
└── my_first_project/
    └── rawdata  /
        └── sub-001  /
            └── ses-001_date-16052024/
                ├── behav/
                │   └── sub-001_ses-001_ephys.bin
                └── ephys/
                    └── sub-001_ses-001_ephys.bin
```

We will 'Upload' data to a central data storage, as you would do during
acquisition. Then, we will 'Download' a subset of data from the central
storage, as you would do during analysis.

This walk-through will give an overview of **datashuttle** functionality. To
see what extra features **datashuttle** can provide, check out the various
[How To](how_tos) pages linked during this walk-through.

## Installing **datashuttle**

The first step is to install datashuttle, by following the instructions
at the [How to Install](install). Once **datashuttle** is installed,
typing `datashuttle launch` will launch the front page in your terminal

[!! IMAGE OF DATASHUTTLE FRONT PAGE !!]

## Make a new project

The first thing to do when using **datashuttle** on a new machine is
to set up your project.

We need to tell **datashuttle** the

1) project name
2) the location on our local machine where we will put the acquired data
3) the location of the central data storage where we will upload the acquired data

**datashuttle** can support central data storage mounted on the local machine
or through an SHH connection. For more detail on connecting to a mounted drive
or SSH connection, see the [How to Setup a New Project]() page.

In this walk-through, we will set our _central_ data storage to a
filepath on our machine for simplicity.

First, clicking `Make New Project` will take you to the project setup page

[!! page of empty project setup !!]

We'll call our project 'my_first_project', typing this into the first
input box.

[PICTURE]

Next we need to specify the _local path_, the location on our machine where
we will save our acquired data. You can choose any directory that is
convenient, and end the path with `local`. You can type the path in, copy it with `CTRL+V` or
use the `Select` button to select through a folder tree.

[PICTURE]

Finally, we need to set the _local path_. Usually this would be
a path to a mounted central storage drive or include details for [connecting
with SSH].In this walk through, we will
set this next to the 'local' path to convenience. Copy the contents
of the _local path_ input by hovering over it and pressing `CTRL+Q` to copy
the contents. Then, paste it into the _central path_ input with `CTRL+V`
and change the 'local' to 'central'.

[!! page of filled out project setup !!]

You can now click 'Save' to set up the project. Once the project
is created, a new button will appear `Go to Project Screen`. Click
to move on to the [Create project]() page.

## Creating folders

Let's imagine it's our first day of data collection in a new experiment,
and we are acquiring  behaviour (`behav`) and electrophysiology (`ephys`) data.
We need to create standardised subject, session and datatype folders
to put our data into.

Following the [NeuroBlueprint]() style we will
call the first subject `sub-001`. Additional key-value pairs in the subject
name could be included if desired (see the
[NeuroBlueprint specification]()
for more details).

In the session name we can include today's date,
so our first session will be `ses-001_date-<todays_date>`.

[!! Create Project Page Image !!]

We could start by typing `sub-001` into the subject input box, but
it is more convenient to simply double-left-click it. This will suggest
the next subject number based on the current subjects in the project.
As currently this project is empty, the suggested next subject is `sub-001`.

[!! ADD PHOTO !!]

```{note}
The subject and session folder input boxes have live validation.
This will flag any [NeuroBlueprint]() errors with a red border
(for example, if you accidentally try to create a duplicate subject or session).
```

Next, we can input the session name. Double-left-click on the session
input to automatically fill with `ses-001`. We can then add
today's date with the `@DATE@` convenience tag.

[!! ADD PHOTO !! ]

When the session folder is created, today's date will be automatically added.

Next, uncheck the `funcimg` and `anat` datatype boxes, to ensure
we only create `behav` and `ephys` folders in our session folder.

[ !! Photo !! ]

Finally, click `Create Folders` to create the folder structure in the project!

For additional validations, check out our [How to use folder name templates]() page.
For a full list of convenience tags, check out [How to create folders]().

## Exploring folders

In our imagined experiment, we will next want to save data from
data acquisition software into our newly created, standardised folders.

When folders are created, the `DirectoryTree` will update to display the
new folders. By hovering over a subject or session folder on
the directory tree we can quickly copy the full path to the folder (`CTRL+Q)`).

Alternatively, pressing `CTRL+O` will open the folder in your file browser.

These shortcuts aim to make it simple to direct your acquisition software
to the created session datatype folders. However over the `DirectoryTree`
for a tooltip indicating all possible shortcuts.

```{admonition} Creating mock data for the walk-through

To continue with our experiment, we will need to create 'mock'
acquired data to transfer to central data storage.

Hover over the `behav` folder the `DirectoryTree` with your
mouse and and press `CTRL+O` to open folder in your file browser.
Do the same with the `ephys` folder.
Next download mock behaviour and ephys data from
[this link]()—and drag and drop
the mock data into the relevant folders.

Alternatively, you can create mock data by creating empty text files
in your favourite text editor.

[!! Expected File Tree !!]
```

## Uploading to central storage

Now we have 'acquired' `behav` and `ephys` data on this machine.
The next step is to upload it to the central data storage. Typically,
this would be and external machine or server, connected through a mounted
drive or via SSH. In this walk-through, we set the _central path_ on the same
machine for convenience.

Switch to the 'Transfer' tab

[!! Image of transfer tab !!]

This first page allows us to upload the entire project, both the `rawdata`
and `derivatives` (the `derivatives` folder is used for preprocessing outputs,
see the [NeuroBlueprint specification]()).
As we only have a `rawdata` folder, we can simply click `Transfer` to
upload everything to central storage.

Navigating to the _central path_ in the file browser,
the newly transferred data will have appeared.
(An easy way to navigate here is to go to the
`config` tab and press `CTRL+O` on the _central path_ input box).

```{warning}
The `Overwrite Existing Files` checkbox on the transfer tab is an important
setting. By default it is turned off and a transfer will never overwrite a
file that already exists, even if the source version is newer.

For example if we upload the first session's behavioural data, and there
is already a file on central storage with the same name and in the same folder,
the file will not be uploaded.

If 'Overwrite Existing Files' is on, then any existing files
will be overwritten by newer versions of the file during transfer.
```

If we did have a `derivatives` folder, we could click the `top-level-folder`
or `custom` button for refined transfer. For more information
see [How to Transfer Data]() and the next section for `custom` transfers.

With the data safely on our central storage,
our experimental acquisition session is complete!

## Downloading from central storage

Finally, let's imagine we are on a new, analysis machine and want to
download a subset of data for preprocessing and analysis. In this example
we will want to grab the behavioural data from the second session only—
however the custom interface can be used for refined transfer when there
are many subjects and sessions e.g. downloading the 'test' sessions
from a specific range of subjects.

```{note}
To replicate starting on a new local machine, delete the 'rawdata' folder from
your 'local' folder. We will now 'download' data from the _central path_
to our now empty local folder.
```

The custom data transfer screen has options for selecting specific subjects,
sessions and data-types. We will look at a small subset of possible options here,
for more information see [How to perform a custom transfer]().

[!! custom transfer screen !!]

In the subject input, we can simply put "all" to download all subjects
(in this case, we only have one subject anyway).

In the session input, let's grab only the second session. We can use the
wildcard tag to avoid having to type out the exact date:
`sub-002_@*@`.

Next, let's select only the `behav` datatype from the datatype checkboxes.

Note that the 'Overwrite Existing Files' setting affects both uploads
and downloads—if on, any local versions of a file will be overwritten
by newer versions downloaded from central storage.

Finally, we can select 'Download' from the upload / download switch,
and press 'Transfer'. The transfer will complete, and the custom selection
of files will be available in the 'local' folder

```{note} Inpsecting Output Logs
Logs with detailed information on data transfers (as well as file creation
and config changes) are stored in logs. Visit the [How to Read the Logs]()
page for more information
```

And that just about does it! More features, see the hiow to. Otherwise
please jump in. Don't hestiate to get in contact XXX contact liks.
