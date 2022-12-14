from datashuttle.utils.directory_class import Directory


def get_directories(cfg) -> dict:
    return {
        "ephys": Directory(
            name="ephys",
            used=cfg["use_ephys"],
            level="ses",
        ),
        "behav": Directory(
            name="behav",
            used=cfg["use_behav"],
            level="ses",
        ),
        "funcimg": Directory(
            name="funcimg",
            used=cfg["use_funcimg"],
            level="ses",
        ),
        "histology": Directory(
            name="histology",
            used=cfg["use_histology"],
            level="sub",
        ),
    }
