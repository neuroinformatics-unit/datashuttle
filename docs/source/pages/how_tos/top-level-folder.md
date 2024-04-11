(how-to-set-top-level-folder)=

# How to Set the Top-level Folder

 [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/) specifies
the top-level folder inside the project folder must be `rawdata` or `derivatives`.

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

In **datashuttle**, the top level folder is relevant when:
1) creating folders (i.e. in `rawdata` or `derivatives`)
2) transferring data with the top-level method or custom.

Using the Graphical interface, the top-level folder is
set by a drop-down menu on the relevant tab (`Create` or `Transfer`).
^^ TODO: link to sections!!!  TODO TODO TODO


However, in the Python API methods act in `rawdata` or `derivatives`
according to a stored top-level folder setting.

## Setting the level folder in the Python API

In the Python API the *working* top level folder
is stored as a persistent property, accessible with
the `get_top_level_folder()` and `set_top_level_folder()` methods.

This is to avoid continuously inputting the top-level folder
for every method call.

:::{info}
:class: info

Top-level folder is persistent across sessions on a machine. If you
change the working top-level folder with `set_top_level_folder()` then
close-and-reopen python, the change is remembered.

Changing the working top-level folder only affects the
project on the local machine you are using.

:::

When making folders, `create_folders` will only create folders in the
working top-level folder.

Transferring folders (e.g. with `upload_custom()` or `download_custom()`) will
only transfer folders in the working top-level folder
(unless `upload_entire_project()` or `download_entire_project()` is used).

In the below example we will create and transfer folders in `rawdata`.
Then, the top-level folder is switched to `derivatives` and the actions repeated.#

```python
project.set_top_level_folder("rawdata")

# make folders in `rawdata`
project.create_folders(sub="sub-002")

# transfer files in `rawdata`
project.upload_data(sub_names="all", ses_names="all", datatype="all")

# set working top-level folder to `derivatives`
project.set_top_level_folder("derivatives")

print(project.get_top_level_folder())
# "derivatives"

# create folders in derivatives
project.create_folders("sub-002")

# transfer folders in derivatives
project.download_data()

```
