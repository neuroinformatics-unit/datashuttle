
# How to Update Configs

The project configs can be updated at any time following the initial setup.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/updating-configs-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/updating-configs-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

Clicking the `Configs` tab on the `Project Manager` page will display
the current configs.

Changing any config and clicking `Save` will  update the project
configs on the local machine.

If SSH configs are changed the connection may need to be
[setup again](new-project-ssh).

:::

:::{tab-item} Python API
:sync: python

The project configs on the local machine can be selectively
updated with the `update_config_file()` method.

For example, to change the `local_path` and `central_path`:

```python
project.update_config_file(
    local_path="/a/new/local/path",
    central_path="/a/new/central/path"
)
```

If SSH configs are changed the connection may need to be
[setup again](new-project-ssh) with:

```python
project.setup_ssh_connection()
```

:::
::::
