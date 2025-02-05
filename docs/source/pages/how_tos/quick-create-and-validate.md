# How to make a local project

To get started quickly with **datashuttle**, you can pass a path to your project
and immediately perform validation (against the NeuroBlueprint standard)
and create folders.

First, we can import **datashuttle** and set up a project with the ``project_name``.
If a project already exists, this should match the project folder name (i.e. the level above ``rawdata``).

```python

from datashuttle import DataShuttle

project = DataShuttle("my_project_name")

```

Next, we give **datashuttle** the path to the project folder (this can, but doesn't have to, include
the ``project_name```)

```python

project.make_config_file(
    local_path=r"C:\MyUsername\my_data\my_project_name"
)

```

The project is now ready for use, and in future, can be instantiated only
with the line ``project = DataShuttle("my_project_name")`` (i.e. you will not
have to set the `local_path` again).

If you wish to change the project settings at a later time, use ``project.update_config_file()``.

For example, it is possible to immediately validate the project:

```python
project.validate_project("rawdata", error_or_warn="warn")
```

Setting ``error_or_warn`` will display all validation issues, otherwise
it will error on the first one encountered.

New project folders can also be created in the local folder:

```python
project.create_folders("rawdata", "sub-001", "ses-001_@DATE@", datatype=["ephys", "behav"])
```

see [](how-to-create-folders) for more detail on folder creation.

:::{note}

When setting only the `local_path` only, some functionality of **datashuttle** is lost.
It will not be possible to:
- transfer data, which requires passing configs related to a central project. See
[](how-to-transfer-data) and [](make-a-new-project_target) for more information.
- Any method that exposes a ``local_only`` argument will always set this to ``True``.
For example, validation will only ever be performed on the local project.
:::
