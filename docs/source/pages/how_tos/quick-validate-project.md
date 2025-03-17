(quick-validate-projects)=

# How to Quickly Validate an Existing Project

# TODO: add image of TUI, use same path as in the API + outputs
# Show the same outputs for the TUI in comments!

Datashuttle provides the functionality to validate an existing NeuroBlueprint project.
All NeuroBlueprint issues will be flagged, including a filepath pointing to
problematic folders.

Below, we explore how to quickly validate a NeuroBlueprint project without
setting up a full project in **datashuttle**.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

To quickly validate a project, start the terminal user interface with
``datashuttle launch`` and click ``"Validate Project at Path"``.

This will open the screen below. To validate an existing project,
enter the full filepath to the project folder in the top input box
and click ``Validate``:

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

Any validation errors detected in the project will be displayed in the logging box.
See ``Strict Mode` below for key details on how the validation is performed.

**Options**

Top level folder dropdown
: The top-level folder to validate the folders within.

Strict Mode
: If `True`, only allow NeuroBlueprint-formatted folders to exist in
the project. By default, non-NeuroBlueprint folders (e.g. a folder
called 'my_stuff' in the 'rawdata') are allowed, and only folders
starting with sub- or ses- prefix are checked. In `Strict Mode`,
any folder not prefixed with sub-, ses- or a valid datatype will
raise a validation issue.

:::

:::{tab-item} Python API
:sync: python

To validate a project using the Python API, pass the path
to the project to validate to ``quick_validate_project``:

```python
from datashuttle import quick_validate_project

quick_validate_project(
    project_path="/mydrive/path/to/project/project_name",
    display_mode="error",
)

```

The function [](datashuttle.quick_validate_project) can be used to quickly validate a project fully conforms
to the[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) standard. This does not require setting up
a full ``datashuttle`` project, only the filepath to the project.

See [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) API documentation at the link, including
the important parameter ``strict_mode`` which controls how validation is performed.

:::

::::
