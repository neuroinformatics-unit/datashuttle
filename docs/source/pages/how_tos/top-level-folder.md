(how-to-set-top-level-folder)=

# How to set Top Level Folder

The [NeuroBlueprint]() specficiation the top-level folder inside the
project folder must be `rawdata` or `derivatives`.

`rawdata` is where acquired, raw data goes and it is never changed.
`derivatives` is where anything processing goes (and does not necessarily
need to be formatted in neuroblueprint style).

In **datashuttle**, the top level folder is relevant when
1) creating folders (i.e. in `rawdata` or `derivatives`)
2) transferring data with the top-level method or custom.

When using the Graphical interface, the top-level folder is
set by the drop-down menu on the relevant tab (Create or Tansfer).
However, in the Python API methods act depending on the set
'top level folder'.

# Setting the level folder in the Python API

In the Python API the 'working' top level folder
is held as a variable ont he class. The `make_folders`
and upload and download functions (example) will
act relate to top-level folder.

The working top-level folder is used to avoid entering
it every time you make folders or transfer data.

The `get_top_level_folder()` and `set_top_level_folder()`
can be used to get and set the working top level folder respectively.

In the below example we weill create and transfer folders in `rawdata`.
Then we will switch to do the same in `derivatives`.

```python
project.set_top_level_folder("rawdata")

# make folders in `rawdata`
project.make_folders(sub="sub-002")

# transfer files in `rawdata`
project.upload_data(sub_names="all", ses_names="all", datatype="all")

# set working top-level folder to `derivatives`
project.set_top_level_folder("derivatives")

print(project.get_top_level_folder())
# "derivatives"

# create folders in derivatives
project.make_folders("sub-002")

# transfer folders in derivatives
project.download_data()

```
