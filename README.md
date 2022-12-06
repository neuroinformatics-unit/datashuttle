# SWC Data Management Tool

- Convenient GUI / Python API / Command line interface Tool for project data management
- Generate standardized directory trees for projects, convenient when collecting new data
- Automatically sync data between local and remote storage after collection
- Convenient API for transfering data between local and remote hosts

### Directory Tree

Below is an suggested folder structure based on the BIDS framework. BIDS is a data organisation format widely used in neuroimaging and human electrophysiology [[1]](https://www.nature.com/articles/s41597-019-0105-7) that has recently begun extending to animal electrophysiology [[2]](https://neurostars.org/t/towards-a-standard-organization-for-animal-electrophysiology-a-new-bids-extension-proposal/18588).

Each mouse directory is formatted as sub-XXX (e.g. sub-001) and eachs session is formatted ses-XXX (e.g. ses-001).

```
└── project_name/
    └── raw_data/
        ├── ephys/
        │   └── mouse/
        │       └── session/
        │           └── behav/
        │               └── camera
        ├── behav/
        │   └── mouse/
        │       └── session/
        └── microscopy/
            └── mouse/
```
