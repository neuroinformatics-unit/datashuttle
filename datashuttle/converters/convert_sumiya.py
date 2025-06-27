"""Custom converter to NeuroBlueprint.

In datashuttle, `project.convert(path_to_module)` can take a custom converter to allow
conversion of non-NeuroBlueprint formats to NeuroBlueprint.

To write a custom converter, create a new module that includes the function
`converter_func(project)` that takes the current datashuttle `project` as an input.
When `project.convert(path_to_module) is called, the project will be passed
to this custom convter function. You then have access to the current project
and can detect and convert your non-NeuroBlueprint folders.

Within the converter function, you can use `local_path = project.get_local_path() / "rawdata"`
to get the current local path. You can glob for folders formatted to your style, and
iterate through them to convert.

Often, you may collect new sessions in a non-NeuroBlueprint format for subjects
that are already in NeuroBlueprint format. `project` has a number of convenience
functions to return the state of the project and infer the NeuroBlueprint subject names.

For example, `project.get_sub_names_from_key_value_pair(key, value)` will return
subject names that include any given key-value pair. You can use this to match
identifiers from your format to an existing NeuroBlueprint format name with
that identifier as a key-value pair. It is therefore recommended to include unique
subject identifiers from your format as a field in the subject folder name
e.g. `sub-001_myID-1324`.

If the subject does not exist, you can use `project.get_next_sub()` to return
the next NeuroBlueprint subject id e.g. sub-002. You can then append your format
id to the subject name.

To find the next NeuroBlueprint session ID, you can use `project.get_next_ses()`.
Then, you can place output folders into NeuroBlueprint datatype folders.

Once you have your NeuroBlueprint subject, session names and paths to
the datatype folders, you can create a new tree, move the data, and
delete the old (now empty) folders.

`project.convert()` starts a logger than can be
accessed with `project.log_and_message()` or `project.log_and_raise_error()`.
The corresponding log file is saved with the rest of the datashuttle logs.
"""

import shutil
from datetime import datetime

import yaml

# TODO: test some more complex cases, add proper tests.
# TODO: could do a check here that all dates are older than this one
# TODO: add to general validation, that all date / datetime keys are in order e.g. ses-001 must be later than ses-002


def get_mapping():
    return {
        "ExperimentEvents": "behav",
        "SessionSettings": "behav",  # TODO: convert this to a metadata file, we will add metadata spec soon
        "VideoData": "behav",
    }


def converter_func(project):
    """Convert Aeon-formatted Bonsai output to NeuroBlueprint.

    `project.convert()` starts a logger than can be
    accessed with `project.log_and_message()` or `project.log_and_raise_error()`.
    The corresponding log file is saved with the rest of the datashuttle logs.

    First, search for all folders in the local "rawdata" path.
    Folders that are a valid ISO8601 datetime are assumed to be
    Aeon-formatted sessions. Iterate through these sessions
    and convert them to NeuroBlueprint.

    For each session, find the Aeon subject ID from the .yaml file.
    Use this in the subject name e.g. `sub-001_id-plimbo`.
    Check if thus subject already exists in the NeuroBlueprint project,
    if so then use that, otherwise create a new subject based on
    `project.get_next_sub()`.

    Create a session name as ses-..._datetime-...where datetime is the Aeon
    session folder name. Use `project.get_next_ses()` to find the NeuroBlueprint
    session ID if the subject already exists, otherwise just use `ses-001_datetime-...`.

    Next, use the `get_mapping()` dictionary to map Aeon device folders to their
    NeuroBlueprint datatypes. Now we have the subject, session and datatype name
    for a given decide folder, so we can move it to a new NeuroBlueprint folder.

    Once all device folders are moved, delete the old Aeon folder tree. It assumes
    all files have been moved, if any remain an error is raised.
    """
    rawdata_path = project.get_local_path() / "rawdata"

    aeon_session_folders = []

    # Find all folders in the project that are aeon format (datetime)
    for item in rawdata_path.glob("*"):
        if item.is_dir() and item.name[:4] != "sub-":
            try:
                datetime.fromisoformat(item.name)
            except ValueError:
                continue

            aeon_session_folders.append(item)

    # Confidence check the folders are sorted by datetime, otherwise
    # the session ids for per-session conversion will go out of order.
    assert aeon_session_folders == sorted(
        aeon_session_folders, key=lambda p: p.stat().st_ctime
    )

    # Convert each session
    for session_folder in aeon_session_folders:
        convert_aeon_session_folder(project, session_folder)


def convert_aeon_session_folder(project, input_folder):
    """Move a single Aeon session to NeuroBlueprint folder."""
    # Process the aeon session folder name to daetime
    aeon_ses_name = input_folder.name

    datetime_ = datetime.fromisoformat(aeon_ses_name)
    formatted_datetime = datetime_.strftime("%Y%m%dT%H%M%S")

    # Find the subject in the Aeon session
    session_yaml_path = input_folder / "SessionSettings" / "session.yaml"

    if not session_yaml_path.is_file():
        project.log_and_raise_error(
            f"Cannot find session.yaml for input session {input_folder}. Cannot convert.",
            FileNotFoundError,
        )

    with open(input_folder / "SessionSettings" / "session.yaml") as f:
        aeon_subject_id = yaml.safe_load(f)["animalId"]

    # If the subject already exists, then get the full NeuroBlueprint
    # subject name and next available session id. Otherwise, create a new
    # name and use session id 001.
    if sub_name := project.get_sub_names_from_key_value_pair(
        "id", aeon_subject_id
    ):
        assert len(sub_name) == 1, (
            f"Multiple folders detected with the same unique aeon subject id: {aeon_subject_id}."
        )
        sub_name = sub_name[0]

        ses_id = project.get_next_ses("rawdata", sub=sub_name)
        ses_name = f"{ses_id}_datetime-{formatted_datetime}"

    else:
        sub_id = project.get_next_sub("rawdata")
        sub_name = f"{sub_id}_id-{aeon_subject_id}"
        ses_name = f"ses-001_datetime-{formatted_datetime}"

    # Create the paths for the new NeuroBlueprint folder
    nb_sub_path = project.get_local_path() / "rawdata" / sub_name
    nb_ses_path = nb_sub_path / ses_name

    # For each device, get its datatype and move it
    # to the new NeuroBlueprint folder
    aeon_device_folders = list(input_folder.glob("*"))

    datatype_mapping = get_mapping()

    for device_folder in aeon_device_folders:
        if device_folder.name in datatype_mapping:  # use get
            datatype = datatype_mapping[device_folder.name]

            nb_datatype_path = nb_ses_path / datatype
            nb_datatype_path.mkdir(parents=True, exist_ok=True)

            project.log_and_message(
                f"Moving folders:\nsource: {device_folder.as_posix()}\ntarget: {nb_datatype_path.as_posix()}"
            )

            shutil.move(device_folder, nb_datatype_path)

    # Delete the original folder. We can make this crash
    # if there are files remaining instead of using rmtree
    if any([file for file in input_folder.rglob("*") if f.is_file()]):
        project.log_and_raise_error(
            f"Session {aeon_ses_name} is not empty after conversion, cannot delete.",
            RuntimeError,
        )
    else:
        shutil.rmtree(input_folder)  # TODO: input folder path?
