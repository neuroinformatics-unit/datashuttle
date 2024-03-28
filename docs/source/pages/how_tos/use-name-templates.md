(how-to-use-name-templates)=

# How to use Name Templates

Validation in **datashuttle** is by default restricted to the
NeuroBlueprint specification. Any subject or session names
that are not formatted correctly (e.g. not starting with
"sub-" or "ses-" will be flagged.

However, it is also possible to add custom templates to validate against
by defining template names using 'regular expressions'.

For example, say you wanted your subjects to be in the form
`sub-XXX_id-XXXXXX` where `X` is a digit (i.e. subject number with
a 6-digit id.

We can define this
as a regexp where `\d` stands for 'any digit`:

```python
"sub-\d\d\d_id-\d\d\d\d\d\d"
```

If this is defined as a Name Template, any name that
does not take this form will result in a validation error.

## Set up Name Templates
::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui

```{image} /_static/screenshots/how-to-name-templates-dark.png
   :align: center
   :class: only-dark
   :width: 900px
```
```{image} /_static/screenshots/how-to-name-templates-light.png
   :align: center
   :class: only-light
   :width: 900px
```
<br>


Click the `Settings` button in the `Create` tab. Scroll down to the
`Template Validation` section.

Clicking the checkbox will turn on `Template Validation` and these
can be set for subject and session independent. If the input is left empty,
no name template will be applied.

Fill in the subject or session name template—any changes
will be automatically saved. These settings will persist across
**datashuttle** sessions.

:::

:::{tab-item} Python API
:sync: python

The `set_name_templates()` and `get_name_templates()` can be used
to set and get current name template settings.

`set_name_templates` takes as input the `name_template` dictionary,
which is formatted as below:

```

name_templates = {
    "on": True,
    "sub": "sub-\d\d\d_id-\d\d\d\d\d\d",
    "ses": None,
}


project.set_name_templates(
    name_templates
)

```

In the above example, validation with name templates is
turned on `"on: True`. A template is set for the subject name,
but no template is set for the session name.


:::

::::


## Name Template placeholders

Placeholders (based on [regular expressions]) can be used to
fill templates with yet-unknown values.

Any regular expression available in  Python is permitted,
but below we summarise the most useful:

Wildcard Single Digit:
: `\d` can act as a placeholder for a digit. \
*e.g.* `sub-\d\d\d` will allow any `sub-` prefix followed by three digits.

Wildcard Single Character:
: `.?` can act as a placeholder for any character \
*e.g.* `sub-\d\d\d_id-.?.?.?.?` will allow the `id-` to be made up for any 4-character id.

Wildcard Range:

: `.*` can act as a placeholder for an unknown range. \
*e.g.* `sub-\d\d\d_id-.*` will allow the `id-` to be made up of any length combination of any characters.
