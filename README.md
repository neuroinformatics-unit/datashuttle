# DataShuttle

Datashuttle is a work in progress and is currently in alpha release v0.1.0.

![datashuttle_figure_machines](https://github.com/neuroinformatics-unit/datashuttle/assets/29216006/51b65a6d-492a-4047-ae7b-16273b58e258)

Datashuttle includes tools for automated generation and transfer of neuroscience project folders formatted to the [SWC-Blueprint specification](https://swc-blueprint.neuroinformatics.dev/).

* Manage files across multiple data-collection computers by synchronising all data to with a centrally stored project.

* Simplify data transfers by selecting only a sub-set of data to move (e.g. specific subjects, sessions or datatypes)

See the [DataShuttle Documentation](https://datashuttle.neuroinformatics.dev) to get started or join the [Zulip chat](https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle) to discuss any questions, comments or feedback.

## Installation

DataShuttle is hosted on  [PyPI](https://pypi.org/project/datashuttle/) and can be installed with pip.

`pip install datashuttle`

Datashuttle required Rclone for data transfers. The easiest way to install Rclone is using [Miniconda](https://docs.conda.io/en/main/miniconda.html):

```
conda install -c conda-forge rclone
```

See [the Rclone website](https://rclone.org/install/) for alternative installation methods.

## SWC-BIDS Folder Tree

DataShuttle project folders are managed according to SWC-BIDS (example below).
See the SWC-BIDS [specification](https://swc-bids.neuroinformatics.dev/) for more details.

```
└── project_name/
    └── raw_data/
        ├── sub-001/
        │   └── ses-001/
        │   │   ├── ephys/
        │   │   └── behav/
        │   └── anat/
        └── sub-002/
            └── ses-001/
            │   ├── behav/
            │   └── imaging/
            └── ses-002/
            │   └── behav/
            └── anat/
```


```+
└── project_name/
    └── rawdata/
        ├── sub-001  /
        │   ├── ses-001/
        │   │   ├── ephys
        │   │   └── behav
        │   └── anat
        └── sub-002/
            ├── ses-001/
            │   ├── behav
            │   └── imaging
            ├── ses-002/
            │   └── behav
            └── anat
```
