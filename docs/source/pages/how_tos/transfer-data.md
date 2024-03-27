(how-to-transfer-data)=
# How to Transfer Data

Transferring data between the local project and the project located
on central storage is a key feature of **datashuttle**. It allows:

- Transfer of data from an acquisition machine to the central project.
- Convenient integration of data collected from multiple acquisition.
- Pulling subsets of data from central storage to analysis machines.

TODO: NEED TO MAKE DARK MODE!!

```{image} _static/datashuttle-overview.png
:alt: My Logo
:class: logo, mainlogo
:align: center
:width: 600
```
<br>

:::{admonition} Transfer Direction
:class: note


In **datashuttle**, the term *upload* refers to transfer
from the local machine to central storage.
*Download* refers to transfer from central storage to
a local machine.
:::

There are three main emthods to transfer data in **datashuttle**. These
allow transfer between:

1) The entire project (all files in both `rawdata` and `derivatives`)
2) A specific top-level-folder (e.g. all files in `rawdata`)
3) A custom subset of subjects / sessions / datatypes.

Below we will explore each method in turn.

(transfer-entire-project)=
## Transfer entire project

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui
test1
:::

:::{tab-item} Python API
:sync: python
test1
:::

::::

(transfer-top-level-folder)=
## Transfer top-level-folder

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui
test1
:::

:::{tab-item} Python API
:sync: python
test1
:::

::::

(making-custom-transfers)=

## Custom transfers

::::{tab-set}

:::{tab-item} Graphical Interface
:sync: gui
test1
:::

:::{tab-item} Python API
:sync: python
test1
:::

::::

### Convenience Tags

(transfer-the-wildcard-tag)=

TODO: rename to general convenience tag
