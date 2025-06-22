def tags(tag_name: str) -> str:
    """Return the formatting tag used for subject/session name parsing.

    If changing the formatting of these tags, update the dict values here.
    """
    tags = {
        "date": "@DATE@",
        "time": "@TIME@",
        "datetime": "@DATETIME@",
        "to": "@TO@",
        "*": "@*@",
    }
    return tags[tag_name]
