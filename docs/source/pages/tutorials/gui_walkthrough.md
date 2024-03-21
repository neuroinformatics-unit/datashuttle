(gui_walkthrough)=
# Graphical Walkthrough

1) TODO: add estimated time to complete

## Introduction

This tutorial will give a full introduction to starting
a neuroscience project with **datashuttle**.

We will get an overview of  **datashuttle**'s key features by creating
and transferring a 'mock' experiment, standardised to the
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) style.


```{image} /_static/screenshots/tutorial-1-example-file-tree-dark.png
   :align: center
   :class: only-dark
   :width: 550px
```
```{image} /_static/screenshots/tutorial-1-example-file-tree-light.png
   :align: center
   :class: only-light
   :width: 550px
```
<br>

We will create standardised folders then upload 'acquired' data (empty text files)
to a central data storage, as you would do in a typical data acquisition session.
Then we will download a subset of data (e.g. test sessions only) from the central
storage, as you would do during analysis.

## Installing **datashuttle**

The first step is to install **datashuttle**, by following the instructions
at the [How to Install](how-to-install).


::::{tab-set}

:::{tab-item} Graphical Interface
Once **datashuttle** is installed,  typing `datashuttle launch` will
launch the application in your terminal

```{image} /_static/screenshots/tutorial-1-landing-screen-dark.png
   :align: center
   :class: only-dark
   :width: 700px
```
```{image} /_static/screenshots/tutorial-1-landing-screen-light.png
   :align: center
   :class: only-light
   :width: 700px
```

:::
:::{tab-item} Python API
test
:::
::::

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

::::{tab-set}

:::{tab-item} Graphical Interface

Now we will set up a new project. Click `Make New Project` and you
will be taken to the project setup page.

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

We'll call our project `my_first_project`, and can type this into
the first input box on the page.

```{image} /_static/screenshots/tutorial-1-make-project-name-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-make-project-name-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Next we need to specify the _local path_, the location on our machine where
we will save our acquired data. Choose any directory that is
convenient, and then add `local` to the end of the filepath.
The filepath can be typed into the input, copied in with `CTRL+V`
or selected from a directory tree using the `Select` button.

```{image} /_static/screenshots/tutorial-1-make-local-path-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-make-local-path-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Finally, we need to  select the _local path_. Usually this would be
a path to a mounted central storage drive or relative to the server path
if connecting via SSH. In this tutorial, we will
set this next to the _local path_ for convenience:

1) Copy the contents of the _local path_ input by hovering over it and pressing `CTRL+Q` to copy.
2) Paste it into the _central path_ input with `CTRL+V` and change 'local' to 'central'.

```{image} /_static/screenshots/tutorial-1-make-central-path-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-make-central-path-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

You can now click `Save` to set up the project. Once the project
is created, the `Go to Project Screen` button will appear.
Click to move on to the `Create Project` page.

:::

:::{tab-item} Python API
test
::::
## Creating folders

Let's imagine today is our first day of data collection,
and we are acquiring  behaviour (`behav`) and electrophysiology (`ephys`) data.

::::{tab-set}

:::{tab-item} Graphical Interface

We will create standardised subject, session and datatype folders
to put our data into using the `Create` tab.

```{image} /_static/screenshots/tutorial-1-create-screen-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/tutorial-1-create-screen-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

Following the [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)
style we will  call the first subject `sub-001`. Additional key-value pairs in
the subject name could be included if desired (see the
[NeuroBlueprint specification](https://neuroblueprint.neuroinformatics.dev/specification.html)
for more details).

In the session name we can include today's date,
so our first session will be `ses-001_date-<todays_date>`.

We could start by typing `sub-001` into the subject input box, but
it is more convenient to simply double-left-click it. This will suggest
the next subject number based on the current subjects in the project.
As currently this project is empty, the suggested next subject is `sub-001`.

```{image} /_static/screenshots/tutorial-1-create-subject-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-create-subject-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

```{note}
The subject and session folder input boxes have live validation.
This will flag any
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/)
errors with a red border. Hover over the input box with the mouse
to see the nature of the error.
```

Next, we can input the session name. Double-left-click on the session
input to automatically fill with `ses-001`. We can then add
today's date with the `@DATE@` convenience tag.

When the session folder is created, today's date will be automatically added.

```{image} /_static/screenshots/tutorial-1-create-session-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-create-session-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Next, uncheck the `funcimg` and `anat` datatype boxes, to ensure
we only create `behav` and `ephys` folders in our session folder.

```{image} /_static/screenshots/tutorial-1-create-datatype-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-create-datatype-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Finally, click `Create Folders` to create the folder structure in the project!

:::

:::{tab-item} Python API
test
:::

::::

This was a quick overview of the creating folders functionality—see [How to use Name Templates](how-to-use-name-templates)
and [Create Folder Tags](how-to-create-folders2) for more detail on validation and convenience tags.

## Exploring folders

In our imagined experiment, we will next want to save data from
acquisition software into our newly created, standardised folders.

::::{tab-set}

:::{tab-item} Graphical Interface

When folders are created, the `Directory Tree` on the left-hand side
will update to display the new folders.
By hovering over a folder on the `Directory Tree` we can quickly
copy the full path to the folder (`CTRL+Q)`).

Alternatively, pressing `CTRL+O` will open the folder in your file browser.

```{image} /_static/screenshots/tutorial-1-explore-folders-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-explore-folders-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

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

```

:::

:::{tab-item} Python API
test
:::
::::

## Uploading to central storage

We have now 'acquired' `behav` and `ephys` data onto our local machine.
The next step is to upload it to central data storage.

Typically,  this would be an external machine or server, connected through a mounted
drive or via SSH. In this walkthrough, we set the _central path_ on our
local machine for convenience.

::::{tab-set}

:::{tab-item} Graphical Interface


First, switch to the `Transfer` tab, where on the left we will again
see a `Directory Tree` displaying the local version of the project.

```{image} /_static/screenshots/tutorial-1-transfer-screen-upload-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/tutorial-1-transfer-screen-upload-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

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

:::

:::{tab-item} Python API
test
:::
::::

With the data safely on our central storage,
our experimental acquisition session is complete!


## Downloading from central storage

Finally, let's imagine we are on a different, analysis machine and want to
download a subset of data for further processing. In this example we will
download only the behavioural data from the second session.

In practice **datashuttle**'s custom data transfers work well when there
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

::::{tab-set}

:::{tab-item} Graphical Interface

The `Custom` transfer screen has options for selecting specific combinations
of subjects, sessions and datatypes. We will look at a small subset of possible
options here, but see [How to make Custom Transfers](making-custom-transfers) for more information.

```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-dark.png
   :align: center
   :class: only-dark
   :width: 600px
```
```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-light.png
   :align: center
   :class: only-light
   :width: 600px
```
<br>

In the subject input, we can simply type `all` (in this case, we only have one subject anyway).

```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-subjects-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-subjects-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Next, let's specify to download only the second session.
We can use the [wildcard tag](transfer-the-wildcard-tag) to avoid typing the exact date—`ses-002_@*@`.

```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-sessions-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-sessions-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Then, select only the `behav` datatype from the datatype checkboxes.

```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-datatypes-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-datatypes-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

Finally, we can select `Download` from the upload / download switch,
and click `Transfer`.

Note that the `Overwrite Existing Files` setting affects both upload
and downloads—any local versions of a file will be overwritten
by newer versions downloaded from central storage when it is turned on.

```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-switch-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/tutorial-1-transfer-screen-custom-switch-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

The transfer will complete, and the custom selection
of files will now be available in the _local path_ folder.

```{note}
Detailed information on data transfers can be found in the `Logs` tab.
Visit [How to Read the Logs](how-to-read-the-logs) for more information.
```

:::

:::{tab-item} Python API
test
:::
::::

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
