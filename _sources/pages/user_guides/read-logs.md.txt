(how-to-read-the-logs)=

# Read the logs

``datashuttle`` stores detailed logs when commands that
create folders, change project configs or perform data transfers are run.

These logs can be accessed and read directly in the
graphical interface, or located on your filesysetm
and opened in your favourite text editor.

Logs are stored as [ISO8601](https://en.wikipedia.org/wiki/ISO_8601)-prefixed
filenames that includes the relevant ``datashuttle`` method performed.

## Find and read the logs
::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-logs-tui-dark.png
   :align: center
   :class: only-dark
   :width: 900
```
```{image} /_static/screenshots/how-to-logs-tui-light.png
   :align: center
   :class: only-light
   :width: 900
```
<br>

The `Logs` tab on the `Project Manager` page displays a list of
all logs for the project.

Double-click on the name of any log file to open it within the
``datashuttle`` graphical interface.

Clicking `Open Most Recent` will open the most recently saved logs.

:::

:::{tab-item} Python API
:sync: python

The path where logs are stored can be accessed by running
`get_logging_path()`:

```python
logs_path = project.get_logging_path()

print(logs_path)
# Path('C:/Users/Joe/data/local/my_first_project/.datashuttle/logs')
```

You can then navigate to this path in your system filebrowser
and open the logs.

```{image} /_static/screenshots/how-to-logs-filesbrowser-dark.png
   :align: center
   :class: only-dark
   :width: 500px
```
```{image} /_static/screenshots/how-to-logs-filesbrowser-light.png
   :align: center
   :class: only-light
   :width: 500px
```
<br>

:::

::::
