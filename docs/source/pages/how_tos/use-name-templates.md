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

:::

:::{tab-item} Python API
:sync: python

:::

::::




## Name Template examples

TODO: double check 

`\d`

`?`

`.*`


