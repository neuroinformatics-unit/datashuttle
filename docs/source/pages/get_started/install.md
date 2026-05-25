(how-to-install)=
# Install

There are two ways to install ``datashuttle``:

1. **Standalone installer** (Windows or macOS) — a single download that
   bundles Python, ``datashuttle``, and all dependencies. **No prior
   Python or conda setup is required.** Recommended for most users.
2. **Python package** (via `conda` or `pip`) — install ``datashuttle``
   into an existing Python environment. Recommended if you already use
   Python and want to script against ``datashuttle``'s API.

## Standalone installer (recommended)

Pre-built installers for the latest release are published on the
[GitHub Releases page](https://github.com/neuroinformatics-unit/datashuttle/releases/latest).
Each release contains three assets — pick the one matching your
operating system and CPU architecture:

| Platform | Asset filename |
|---|---|
| Windows (64-bit) | `datashuttle_<version>.exe` |
| macOS — Apple Silicon (M1 / M2 / M3 / M4) | `datashuttle-<version>-arm64.dmg` |
| macOS — Intel | `datashuttle-<version>-x86_64.dmg` |

`<version>` is the release number — for example, the assets for
release **v0.6.0** are `datashuttle_0.6.0.exe`,
`datashuttle-0.6.0-arm64.dmg`, and `datashuttle-0.6.0-x86_64.dmg`.

::::{tab-set}

:::{tab-item} Windows

Download `datashuttle_<version>.exe` from the
[latest release](https://github.com/neuroinformatics-unit/datashuttle/releases/latest)
and double-click to run the installer. You will be prompted to accept
the MIT licence, then ``datashuttle`` will be installed to
`C:\Program Files (x86)\DataShuttle` with a Start Menu shortcut and
(optionally) a Desktop icon.

To launch, click the **Datashuttle** shortcut — a terminal window will
open and the graphical interface will start automatically.
:::

:::{tab-item} macOS (Apple Silicon)

For Macs with an Apple Silicon chip (M1 / M2 / M3 / M4), download
`datashuttle-<version>-arm64.dmg` from the
[latest release](https://github.com/neuroinformatics-unit/datashuttle/releases/latest).

Open the `.dmg`, accept the MIT licence, then drag **Datashuttle.app**
into your Applications folder.

To check whether you have Apple Silicon, click the Apple menu → *About
This Mac*; the *Chip* field will say "Apple M…".
:::

:::{tab-item} macOS (Intel)

For Intel-based Macs, download `datashuttle-<version>-x86_64.dmg`
from the
[latest release](https://github.com/neuroinformatics-unit/datashuttle/releases/latest).

Open the `.dmg`, accept the MIT licence, then drag **Datashuttle.app**
into your Applications folder.

To check whether you have an Intel Mac, click the Apple menu → *About
This Mac*; the *Chip* / *Processor* field will mention "Intel".
:::

:::{tab-item} Linux

There is no standalone installer for Linux. Install ``datashuttle``
via `conda` or `pip` using the [Python package](#python-package)
instructions below — every Linux distribution ships Python, so the
extra step of running `pip install datashuttle` (plus an `rclone`
install via your distro's package manager or conda) is usually
straightforward.
:::

::::

```{note}
On macOS, the first time you launch a freshly-downloaded
``Datashuttle.app``, macOS Gatekeeper may show a warning. Right-click
the app and choose **Open**, then click *Open* in the dialog — only
needed the first time. Code-signing & notarisation are on the
roadmap.
```

(python-package)=
## Python package

``datashuttle`` requires
[Python](https://www.python.org/)
to run (see [this guide](https://docs.conda.io/projects/conda/en/latest/user-guide/index.html) on managing Python with conda).

The easiest way to install ``datashuttle`` is through the Python package manager
[conda](https://docs.conda.io/en/latest/). However, installation with `pip` is also supported.

### Installation instructions

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
