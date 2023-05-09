# DataShuttle

Datashuttle is a work in progress as has not been officially released. It is not ready for use
as documented, please await first official release.

Datashuttle includes tools for automated generation and transfer of neuroscience project directories formatted to the [SWC-BIDS specification](https://swc-bids.neuroinformatics.dev/).

* Manage files across multiple data-collection computers by synchronising all data to with a centrally stored project.

* Simplify data transfers by selecting only a sub-set of data to move (e.g. specific subjects, sessions or data types)

See the [Documentation Page] for more information, including how to [Get Started]

## Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle required Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.

## SWC-BIDS Folder Tree

DataShuttle project directories are managed according to SWC-BIDS (example below).
See the SWC-BIDS [specification](https://swc-bids.neuroinformatics.dev/) for more details.

```
└── project_name/
    └── raw_data/
        ├── sub-001/
        │   └── ses-001/
        │   │   ├── ephys/
        │   │   └── behav/
        │   └── histology/
        └── sub-002/
            └── ses-001/
            │   ├── behav/
            │   └── imaging/
            └── ses-002/
            │   └── behav/
            └── histology/
```


```+
└── project_name/
    └── rawdata/
        ├── sub-001  /
        │   ├── ses-001/
        │   │   ├── ephys
        │   │   └── behav
        │   └── histology
        └── sub-002/
            ├── ses-001/
            │   ├── behav
            │   └── imaging
            ├── ses-002/
            │   └── behav
            └── histology
```
