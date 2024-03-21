(install)=
# How to Install

**datashuttle** requires Python and a number of other dependencies to run.

The easiest way to install **datashuttle** is through [conda](https://docs.conda.io/en/latest/),
but installation via `pip` and for developers is also supported.

## Installation Instructions

::::{tab-set}

:::{tab-item} Conda

If you do not already have `conda` on your system, first
[download and install conda](https://docs.anaconda.com/free/miniconda/miniconda-install/).

If you are on Windows, the easiest way to use `conda` is through the [Anaconda Prompt](https://docs.anaconda.com/free/anaconda/getting-started/index.html)

Next, create and activate an environment.  You can call your environment whatever you like,
we've used `datashuttle-env`.

```sh
conda create -n datashuttle-env python=3.10
conda activate datashuttle-env
```

then install **datashuttle** and all dependencies with

```sh
conda install -c conda-forge datashuttle
```

:::

:::{tab-item} Pip

**datashuttle** depends on [RClone](https://rclone.org/), which is not available through `pip`.
[Rclone must be installed separately](https://rclone.org/downloads/).

Once Rclone is installed, **datashuttle** and all other dependencies can be
installed in a `pipenv` or `virtualenv` environment with

```shell
pip install datashuttle
```

:::

:::{tab-item} Developers
To get the latest development version, clone the
[GitHub repository](https://github.com/neuroinformatics-unit/datashuttle/)
and then run from inside the repository

```sh
pip install -e .[dev]  # works on most shells
pip install -e '.[dev]'  # works on zsh (the default shell on macOS)
```

This will install the package in editable mode, including all `dev` dependencies.
:::

::::

## Check the installation

To check **datashuttle** has successfully installed, launch the
graphical interface with

```shell
datashuttle launch
```

Before using the graphical interface, you may want to
[choose the best terminal](choose-a-terminal)
for your operating system.
