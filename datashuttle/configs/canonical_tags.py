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
        "DATETO": "@DATETO@",
        "TIMETO": "@TIMETO@",
        "DATETIMETO": "@DATETIMETO@",
    }
    return tags[tag_name]


def get_datetime_formats() -> dict:
    """Get all datetime format strings.

    Returns
    -------
    dict
        A dictionary containing format strings for datetime, time, and date

    """
    return {
        "datetime": "%Y%m%dT%H%M%S",
        "time": "%H%M%S",
        "date": "%Y%m%d",
    }
