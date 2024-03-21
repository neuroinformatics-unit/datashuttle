(gui_walkthrough)=
# Graphical Walkthrough

1) go thrugh with a fine tooth comb - make things extremely simple
2) Partition into shared vs. TUI parts
3) Possibly re-write non-tui parts with the existing python API docs
4) add tui images
5) TODO: add estimated time to complete


## Introduction

This tutorial will give a full introduction to starting
a neuroscience project with **datashuttle**.

We will get an overview of  **datashuttle**'s key features by creating
and transferring a 'mock' experiment, standardised to the
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) style.

```{image} /_static/light-tree.png
   :align: center
   :class: only-light
```

```{image} /_static/light-tree2.png
   :align: center
   :class: only-light
   :width: 533px
```


```{image} /_static/dark-tree.png
   :align: center
   :class: only-dark
```

We will create standardised folders then upload 'acquired' data (empty text files)
to a central data storage, as you would do in a typical data acquisition session.
Then we will download a subset of data (e.g. test sessions only) from the central
storage, as you would do during analysis.

## Installing **datashuttle**

The first step is to install datashuttle, by following the instructions
at the [How to Install](how-to-install). Once **datashuttle** is installed,
typing `datashuttle launch` will launch the application in your terminal

[!! IMAGE OF DATASHUTTLE FRONT PAGE !!]

## Make a new project

The first thing to do when using **datashuttle** on a new machine is
to set up your project.

We need to tell **datashuttle** the:

1) project name
2) location of the project our local machine, where we will save acquired data
3) location of the central data storage, where we will upload the acquired data

**datashuttle** supports central data storage either mounted as a drive
on the local machine or through an SHH connection.
See [How to Make a New Project](make-a-new-project) for detailed instructions for
connecting a mounted drive or SSH connection.

In this walkthrough, we will set our central storage as a
folder on our machine for simplicity.

Now we will set up a new project. Click `Make New Project` and you
will be taken to the project setup page.

[!! page of empty project setup !!]

We'll call our project `my_first_project`, and can type this into
the first input box on the page.

[PICTURE]

Next we need to specify the _local path_, the location on our machine where
we will save our acquired data. Choose any directory that is
convenient, and then add `local` to the end of the filepath.
The filepath can be typed into the input, copied in with `CTRL+V`
or selected from a directory tree using the `Select` button.

[PICTURE]

Finally, we need to  select the _local path_. Usually this would be
a path to a mounted central storage drive or relative to the server path
if connecting via SSH. In this tutorial, we will
set this next to the _local path_ for convenience:

1) Copy the contents of the _local path_ input by hovering over it and pressing `CTRL+Q` to copy.
2) Paste it into the _central path_ input with `CTRL+V` and change 'local' to 'central'.

[!! page of filled out project setup !!]

You can now click `Save` to set up the project. Once the project
is created, the `Go to Project Screen` button will appear.
Click to move on to the `Create Project` page.

## Creating folders

Let's imagine today is our first day of data collection,
and we are acquiring  behaviour (`behav`) and electrophysiology (`ephys`) data.
We need to create standardised subject, session and datatype folders
to put our data into.

Following the
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)
style we will  call the first subject `sub-001`. Additional key-value pairs in
the subject name could be included if desired (see the
[NeuroBlueprint specification](https://neuroblueprint.neuroinformatics.dev/specification.html)
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
This will flag any
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)
errors with a red border.
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
This was a quick overview of the creating folders functionality—see [How to use Name Templates](how-to-use-name-templates)
and [Create Folder Tags](how-to-create-folders2) for more detail on validation and convenience tags.

## Exploring folders

In our imagined experiment, we will next want to save data from
acquisition software into our newly created, standardised folders.

When folders are created, the `Directory Tree` on the left-hand side
will update to display the new folders.
By hovering over a folder on the `Directory Tree` we can quickly
copy the full path to the folder (`CTRL+Q)`).

Alternatively, pressing `CTRL+O` will open the folder in your file browser.

These shortcuts aim to make it simple to direct your acquisition software
to the datatype folders. Hover over the `DirectoryTree`
for a tooltip indicating all possible shortcuts.

```{admonition} Creating mock data for the tutorial

To continue with our experiment, we will need to create 'mock'
acquired data to transfer to central storage. These will
take the form of simple text files with their extensions changed.

You can download these files from
[this link](https://gin.g-node.org/joe-ziminski/datashuttle/src/master/docs/tutorial-mock-data-files),
by right-clicking each file and selecting 'Download (or) Save Link As..'.
Alternatively you can create them in your favourite text editor.

Next, hover over the `behav` folder the `Directory Tree` with your
mouse and and press `CTRL+O` to open the folder in your file browser.
Move the mock behavioural data file (`sub-001_ses-001_camera-top.mp4`)
into the `behav` datatype folder.

Next, repeat this for the `ephys` datatype by moving the remaining
electrophysiology file to the `ephys` folder.

Finally, hover the mouse over the `Directory Tree` and press `CTRL+R` to refresh.

[!! Expected File Tree !!]
```

## Uploading to central storage

We have now 'acquired' `behav` and `ephys` data onto our local machine.
The next step is to upload it to central data storage.

Typically,  this would be an external machine or server, connected through a mounted
drive or via SSH. In this walkthrough, we set the _central path_ on our
local machine for convenience.

First, switch to the `Transfer` tab, where on the left we will again
see a `Directory Tree` displaying the local version of the project.

[!! Image of transfer tab !!]

The first page on the `Transfer` tab allows us to upload the entire project,
both the `rawdata` and `derivatives` (the `derivatives` folder is used for
preprocessing outputs, see the
[NeuroBlueprint specification](https://neuroblueprint.neuroinformatics.dev/specification.html)).

As we only have a `rawdata` folder, we can simply click `Transfer` to
upload everything to central storage.

Navigating to the _central path_ in the file browser,
the newly transferred data will have appeared, simulating transfer
to a separate data storage machine. (An easy way to navigate to the *central path*
is to go to the `Config` tab and press `CTRL+O` on the _central path_ input box).

```{warning}
The `Overwrite Existing Files` checkbox on the transfer tab is an important
setting. By default it is turned off and a transfer will never overwrite a
file that already exists, even if the source version is newer.

For example, if we upload the first session's behavioural data—and there
is already a file on central storage with the same name
in the same folder—the file will not be uploaded.

If `Overwrite Existing Files` is on, then any existing files
will be overwritten by newer versions of the file during transfer.
```

We can also click the `Top Level`
or `Custom` buttons for refined transfers (for example, if we also had a
`derivatives` folder). For more information
see [How to Transfer Data](how-to-transfer-data) and the next section for `Custom` transfers.

With the data safely on our central storage,
our experimental acquisition session is complete!

## Downloading from central storage

Finally, let's imagine we are on a different, analysis machine and want to
download a subset of data for further processing. In this example we will
download only the behavioural data from the second session.

In practice the `Custom` interface works well when there
are many subjects and sessions (for example, downloading only the behavioural
'test' sessions from a specific range of subjects).

```{admonition} Replicating a fresh machine for the tutorial
To replicate starting on a new local machine, delete the `rawdata` folder from
your _local path_. You can press `CTRL+O` while hovering over the `rawdata`
folder on the `Directory Tree` to quickly navigate to it.

We will next download data from the _central path_ to our now-empty local project.
In practice when setting up **datashuttle** on a new machine, you would
again [Make a new project](make-a-new-project).
```

The `Custom` transfer screen has options for selecting specific combinations
of subjects, sessions and datatypes. We will look at a small subset of possible
options here, but see [How to make Custom Transfers](making-custom-transfers) for more information.

[!! custom transfer screen !!]

In the subject input, we can simply type `all` (in this case, we only have one subject anyway).

[ !! Image of subject input !!]

Next, let's specify to download only the second session.
We can use the [wildcard tag](transfer-the-wildcard-tag) to avoid typing the exact date—`ses-002_@*@`.

[ !! Image of session input !!]

Then, select only the `behav` datatype from the datatype checkboxes.

[ !! Image of behav checkbox !!]

Finally, we can select `Download` from the upload / download switch,
and click `Transfer`.

Note that the `Overwrite Existing Files` setting affects both upload
and downloads—any local versions of a file will be overwritten
by newer versions downloaded from central storage when it is turned on.

[ !! Image of upload / download and Transfer input !!]

The transfer will complete, and the custom selection
of files will now be available in the _local path_ folder.

```{note}
Detailed information on data transfers can be found in the `Logs` tab.
Visit [How to Read the Logs](how-to-read-the-logs) for more information¬
```

## Summary

That final transfer marks the end of our **datashuttle** walkthrough!

Now you can:

1) set up a new project
2) upload your acquired data to a central storage machine
3) download subsets of data for analysis

We are always keen to improve **datashuttle**, so please don't hesitate
to get in contact with any
[Issues](https://github.com/neuroinformatics-unit/datashuttle)
or drop in to our
[Zulip Chat](https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle)
with any questions or feedback.

Have a great day!
