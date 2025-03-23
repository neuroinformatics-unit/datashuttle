(set-up-a-local-project)=
# Set up a Local Project

``datashuttle`` can be used to create, validate and transfer
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) projects. In this guide, we will
set up a local-only project that can manage creation
and validation of project folders. This requires
setting up minimal configurations to get started.

To see how a datashuttle project can be set up for transfer,
see the [transfer](how-to-transfer-data) user guide.


::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

Selecting `Make New Project` will take you to the project set up screen.

Enter the name of your project, the path to your project folder and
select `No connection (local only)` (note that the central-path options
are now disabled).

```{image} /_static/screenshots/how-to-make-local-project-configs-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-make-local-project-configs-light.png
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
<br>


See the [create folders](how-to-create-folders) and [validate folders](tutorial-validation)
for details on how to create and validate your project.

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

The project is now ready for use, and in future can be instantiated only
with the line ``project = DataShuttle("my_project_name")`` (i.e. you will not
have to set the `local_path` again).

If you wish to change the project settings at a later time, use ``project.update_config_file()``.

For example, it is possible to immediately validate the project (if it already exists):

```python
project.validate_project("rawdata", error_or_warn="warn")
```

Setting ``error_or_warn`` will display all validation issues, otherwise
it will error on the first one encountered.

New project folders can also be created in the local folder:

```python
project.create_folders("rawdata", "sub-001", "ses-001_@DATE@", datatype=["ephys", "behav"])
```

see  [Create Folders](how-to-create-folders)  for more details.

:::
::::

:::
