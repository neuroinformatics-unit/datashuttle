:html_theme.sidebar_secondary.remove:

# Acquisition script

This script shows how Laura Schwarz (O'Keefe Lab, [Sainsbury Wellcome Centre](https://www.sainsburywellcome.org/web/))
uses ``datashuttle`` to create project folders during the acquisition of a behavioural
task in mice.

```python
def get_file_path():

    # get your project
    project = DataShuttle("social_sleaping")

    # create a prompt to enter the ID number
    # (which we will use to get the subject number)
    id_number = input("Enter ID number: ")
    sub = ID_DICT.get(id_number)

    # get your session number and create a new folder
    # for the session you are about to record.
    # the function get_next_ses() normally checks for the next session
    # if you are recording for a new subject you can use it as well to create
    # the first session folder for this subject.
    session = project.get_next_ses(top_level_folder="rawdata",
                                   sub=f"sub-{sub}_id-{id_number}")

    # create the folders
    created_folders = project.create_folders(
        top_level_folder="rawdata",
        sub_names=f"sub-{sub}_id-{id_number}",
        ses_names=f"{session}_@DATETIME@",
        datatype=["behav"]
    )
    # create a prompt to enter the experiment information and
    # conspecific ID for social experiments.
    # (this is only important for the video file name and might not be
    # relevant for you.)
    exp_number = input("Enter Experiment condition: ")
    comsp_id = input("Enter Conspecific ID: ")

    # print the start of your acquisition
    print(datetime.now())

    # create the video file name
    file_name_video_1 = f"{exp_number}_{comsp_id}.avi"

    # create the path to the video file
    file_path1 = created_folders['behav'][0] / file_name_video_1
    file_path1.touch()

    return file_path1
```
