:orphan:
(validate-project-from-path)=

# Validate a project from a filepath

``datashuttle`` can validate an existing
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html)-formatted project given only the filepath.
All [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) issues will be flagged along with the full filepath
to any problematic folders.

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

To quickly validate a project, start the terminal user interface with
``datashuttle launch`` and click ``Validate Project at Path``.

The screen below will show. To validate an existing project,
enter the full filepath to the project folder in the top input box
and click ``Validate``:

```{image} /_static/screenshots/how-to-quick-validate-project-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-quick-validate-project-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>

Any validation errors detected in the project will be displayed in the logging box.
See ``Strict Mode`` below for details on how the validation is performed.

**Options:**

Top level folder dropdown
: The top-level folder to validate the folders within.

Strict Mode
: If `True`, only [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html)-formatted folders are allowed
in the project. By default, non-[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) folders (e.g. a folder
called `my_stuff` in the `rawdata`) are allowed, and only folders
starting with `sub-` or `ses-` prefix are checked. In `Strict Mode`,
any folder with a name not prefixed with `sub-`, `ses-` or a valid datatype will
raise a validation issue.

:::

:::{tab-item} Python API
:sync: python

To validate a project using the Python API, pass the path
to the project to validate to ``validate_project_from_path``:

```python
from datashuttle import validate_project_from_path

validate_project_from_path(
    project_path="/mydrive/path/to/project/project_name",
    display_mode="error",
)

```

In this case, `display_mode=error` will result in an error on the first encountered validation issue.
Otherwise, `"warn"` will show a python warning for all detected issues, while `"print"` will print directly to the console.

See the [](validate_project_from_path()) API documentation
for full details of parameters, including the important argument ``strict_mode``
that controls how validation is performed.

:::

::::
\
More detail on validation options can be found in the [Validation](tutorial-validation) user guide.
