
# Update configs

The project configs can be updated at any time following the initial set up.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/updating-configs-dark.png
   :align: center
   :class: only-dark
   :width: 1100px
```
```{image} /_static/screenshots/updating-configs-light.png
   :align: center
   :class: only-light
   :width: 1100px
```
<br>

Clicking the `Configs` tab on the `Project Manager` page will display
the current configs.

Changing any config and clicking `Save` will  update the project
configs on the local machine.

If SSH configs are changed the connection may need to be
[set up again](new-project-ssh).

:::

:::{tab-item} Python API
:sync: python

The project configs on the local machine can be selectively
updated with the [](update_config_file()) method.

For example, to change the `local_path` and `central_path`:

```python
project.update_config_file(
    local_path="/a/new/local/path", central_path="/a/new/central/path"
)
```

If SSH, AWS or Google Drive configs are changed the connection
may need to be [set up again](new-project-ssh).

:::
::::

## Delete a project

If you no longer need a project configuration or made a mistake during setup, you can delete it.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

1. Open the project and navigate to the `Configs` tab. Click the `Delete Project` button on the bottom right.

```{image} /_static/screenshots/delete-project-configs-button-dark.png
   :align: center
   :class: only-dark
   :width: 1000px
```
```{image} /_static/screenshots/delete-project-configs-button-light.png
   :align: center
   :class: only-light
   :width: 1000px
```
<br>

2. The deletion confirmation dialog will appear. You can choose between:
   - **Move to Recycle Bin (30 Days)** *(Recommended)*: Moves the project configuration to the Recycle Bin for 30 days.
   - **Permanently Delete**: Permanently removes the project configuration. To prevent accidental deletion, you must type the exact project name.

```{image} /_static/screenshots/delete-project-modal-dialog-dark.png
   :align: center
   :class: only-dark
   :width: 800px
```
```{image} /_static/screenshots/delete-project-modal-dialog-light.png
   :align: center
   :class: only-light
   :width: 800px
```
<br>

3. Soft-deleted projects can be restored or permanently removed at any time from the Main Menu under `Recycle Bin`.

```{image} /_static/screenshots/delete-project-recycle-bin-dark.png
   :align: center
   :class: only-dark
   :width: 1000px
```
```{image} /_static/screenshots/delete-project-recycle-bin-light.png
   :align: center
   :class: only-light
   :width: 1000px
```
<br>

:::

:::{tab-item} Python API
:sync: python

### Move Project to Recycle Bin (Soft Delete)

To soft-delete a project and keep it in the Recycle Bin for 30 days:

```python
from datashuttle import DataShuttle

project = DataShuttle("my_project_name")
project.delete_project(soft_delete=True, retention_days=30)
```

### Restore a Project from Recycle Bin

To restore a deleted project back to active status:

```python
from datashuttle import DataShuttle

DataShuttle.restore_project("my_project_name")
```

### View Deleted Projects in Recycle Bin

To inspect all projects currently in the Recycle Bin:

```python
from datashuttle import DataShuttle

deleted = DataShuttle.get_deleted_projects()
for p in deleted:
    print(
        f"Project: {p['project_name']}, Remaining: {p['remaining_days']} days"
    )
```

### Permanently Delete a Project

To permanently remove a project configuration with typed name confirmation:

```python
from datashuttle import DataShuttle

project = DataShuttle("my_project_name")
project.delete_project(
    soft_delete=False,
    confirm_project_name="my_project_name",
)
```

### Delete Project and Remove Local Data

To permanently delete the configuration and also delete the local data folder:

```python
from datashuttle import DataShuttle

project = DataShuttle("my_project_name")
project.delete_project(
    delete_local_data=True,
    soft_delete=False,
    confirm_project_name="my_project_name",
)
```

:::
::::
