from datashuttle.utils.directory_class import Directory

from .configs import Configs


def get_directories(cfg: Configs) -> dict:

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


def tags(tag_name):
    tags = {
        "date": "@DATE@",
        "time": "@TIME@",
        "datetime": "@DATETIME@",
        "to": "@TO@",
        "*": "@*@",
    }
    return tags[tag_name]
