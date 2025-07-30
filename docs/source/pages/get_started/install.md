(how-to-install)=
# Install

:::{warning}
``datashuttle`` is currently in the [beta](https://en.wikipedia.org/wiki/Software_release_life_cycle#Beta) release phase. Please
get in contact if you encounter any bugs or unexpected behaviour.
:::

``datashuttle`` requires
[Python](https://www.python.org/)
to run (see [this guide](https://docs.conda.io/projects/conda/en/latest/user-guide/index.html) on managing Python with conda).

The easiest way to install ``datashuttle`` is through the Python package manager
[conda](https://docs.conda.io/en/latest/). However, installation with `pip` is also supported.

## Installation instructions

::::{tab-set}

:::{tab-item} Conda

If you do not already have `conda` on your system, first
[download and install conda](https://docs.conda.io/projects/conda/en/latest/user-guide/index.html).

If you are on Windows, the easiest way to use `conda` is through the [Anaconda Prompt](https://docs.anaconda.com/free/anaconda/getting-started/index.html).

Next, create and activate an environment.  You can call your environment whatever you like,
we've used `datashuttle-env`:

```sh
conda create -n datashuttle-env
conda activate datashuttle-env
```

Next, install ``datashuttle`` and all dependencies with:

```sh
conda install -c conda-forge datashuttle
```

:::

:::{tab-item} Pip

``datashuttle`` depends on [RClone](https://rclone.org/), which is not available through `pip`.
[Rclone must be installed separately](https://rclone.org/downloads/).

Once Rclone is installed, ``datashuttle`` and all other dependencies can be
installed in a `pipenv` or `virtualenv` environment with:

```shell
pip install datashuttle
```

:::

:::{tab-item} Developers

`pip` must be used to install developer dependencies.
As
[Rclone](https://rclone.org/)
is not available through `pip`, you can install `Rclone` with `Conda`

```sh
conda install -c conda-forge rclone
```

or using the [RClone's standalone installer](https://rclone.org/downloads/).

Next, clone the ``datashuttle``
[GitHub repository](https://github.com/neuroinformatics-unit/datashuttle/)
to get the latest development version.

To install ``datashuttle`` and its developer dependencies,
run the following command from inside the repository:

```sh
pip install -e .[dev]  # works on most shells
pip install -e '.[dev]'  # works on zsh (the default shell on macOS)
```

This will install an 'editable' version of ``datashuttle``, meaning
any changes you make to the cloned code will be immediately
reflected in the installed package.
:::

::::

## Check the installation

To check ``datashuttle`` has successfully installed, launch the
graphical interface with:

```shell
datashuttle launch
```

Before using the graphical interface, you may want to
[choose the best terminal](choose-a-terminal_)
for your operating system.
