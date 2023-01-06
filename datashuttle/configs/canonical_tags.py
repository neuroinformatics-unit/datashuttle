def tags(tag_name: str) -> str:
    """
    Centralised function to get the tags used
    in subject / session name processing. If changing
    the formatting of these tags, it is only required
    to change the dict values here.
    """
    tags = {
        "date": "@DATE@",
        "time": "@TIME@",
        "datetime": "@DATETIME@",
        "to": "@TO@",
        "*": "@*@",
    }
    return tags[tag_name]
