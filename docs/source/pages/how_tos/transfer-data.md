(how-to-transfer-data)=
# How to Transfer Data

Transferring data between the local project and the project located
on central storage is a key feature of **datashuttle**. It allows:

- Transfer of data from an acquisition machine to the central project.
- Convenient integration of data collected from multiple acquisition.
- Pulling subsets of data from central storage to analysis machines.

```{image} /_static/datashuttle-overview-light.png
:align: center
:class: only-light
:width: 600px
```
```{image} /_static/datashuttle-overview-dark.png
:align: center
:class: only-dark
:width: 600px
```

:::{admonition} Transfer Direction
:class: note


In **datashuttle**, the term *upload* refers to transfer
from the local machine to central storage.
*Download* refers to transfer from central storage to
a local machine.
:::

There are three main methods to transfer data in **datashuttle**. These
allow transfer between:

1) The entire project (all files in both `rawdata` and `derivatives`)
2) A specific top-level-folder (e.g. all files in `rawdata`)
3) A custom subset of subjects / sessions / datatypes.

Below we will explore each method in turn, as well as consider
[configuring transfer](configuring-transfer) including the important
**overwrite existing files** option.

[TODO: Add the overwrite existing folders option here.]

(transfer-entire-project)=
## Transfer the entire project

The first option is to transfer the entire project,
that is all files in the `rawdata` and `derivatives`
[top-level-folders]().  # TODO: LINK TO HOW TO

This includes all files inside or outside a subject, session
or datatype folder.

This mode is useful for data acquisition when **overwrite existing files**
is off. Any new files (i.e. newly acquired data) will be transferred,
to central storage, while any existing files will be ignored.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-transfer-all-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-transfer-all-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

To transfer the entire project navitgate to the `Transfer tab. The
`All` button indicates to transfer the entire project.

Use the `Upload / Download` switch to control transfer direction,
and press `Transfer` to begin.

:::

:::{tab-item} Python API
:sync: python

The command to upload the entire project is

```python
project.upload_entire_project()
```

while the command to download the entire project is

```python
project.download_entire_project()
```

:::

::::

(transfer-top-level-folder)=
## Transfer the top-level folder

This mode acts almost identically to
[transfering the entire project](transfer-entire-project)
however it will only transfer files within a
particular top-level folder (`rawdata` or `derivatives`).

This mode is also useful for quickly uploading new files
during data acquisition (`rawdata`) or analysis (`derivatves`), when
**overwrite existing files** is off—any newly acquired or generated files
will be transfer, ignoring any previously existing files.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui


```{image} /_static/screenshots/how-to-transfer-toplevel-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-transfer-toplevel-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

Selecting the `Top-Level` button on the `Transfer` tab will
allow selection of `rawdata` or `derivatives` to transfer.

Use the `Upload / Download` switch to control transfer direction,
and press `Transfer` to begin.

:::

:::{tab-item} Python API
:sync: python

The `upload_all()` or `download_all()` methods can be used to
upload the current
[working top-level folder](). This is set with the `set_top_level_folder()`.

In the next example, we will upload `rawdata` downloading `derivatives`.


```python
project.set_top_level_folder("rawdata")

print(project.get_top_level_folder())
# "rawdata"

project.upload_all()

project.set_top_level_folder("derivatives")

project.download_all()
```

:::
::::

(making-custom-transfers)=

## Custom transfers


Custom transfers permit full customisation of the files inside
or outside of subject, session and datatype folders.

Custom transfers are particularly useful during data analysis, in
which a subset of data can be downloaded from central storage.
For example, you want to only transfer behavioural data from
test sessions—custom transfers allow you to do this with ease.

See below for how to run custom transfers, as well as
certain keywords and convenience tags to fully customise data transfer.

For example, `all_sub` in the below examples tells datashuttle
to consider only files and folders  within subject folders for transfer.
Files or folders within `rawdata` that are not `sub-`
folders will not be transferred.

See below for full details on custom transfer keywords and
convenience tags.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-transfer-custom-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-transfer-custom-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

Select `Custom` on the `Transfer` tab to select custom transfers.

The top-level folder can be set by the first dropdown menu.

Next, subject and session keywords can be added to customise
files to transfer. In this example, data from all *subject*
folders, all first session behavioral data will be transferred.

Use the `Upload / Download` switch to control transfer direction,
and press `Transfer` to begin.

```{image} /_static/screenshots/how-to-transfer-datatypes-dark.png
   :align: center
   :class: only-dark
   :width: 400px
```
```{image} /_static/screenshots/how-to-transfer-datatypes-light.png
   :align: center
   :class: only-light
   :width: 400px
```
<br>

:::

:::{tab-item} Python API
:sync: python

:::

The `upload_data()` and `download_data()` methods can be used for custom
data transfers. For example, to perform a custom upload:

```python
project.upload_data(
    sub_names="all_sub",
    ses_names="ses-001_@*@",
    datatype="behav",
)
```

In this example, data from all *subject*
folders, all first session behavioral data will be uploaded.

::::

### Custom transfer keywords



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


### Convenience Tags

Tags to include in subject / session names

(transfer-the-wildcard-tag)=
wildcard transfer
: hello world

transfer a range
: hello world

(configuring-transfer)=
## Configuring data transfer

!! overview

!! link to configs
