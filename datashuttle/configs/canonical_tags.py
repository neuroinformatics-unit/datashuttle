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
        "DATETO": "@DATETO@",
        "TIMETO": "@TIMETO@",
        "DATETIMETO": "@DATETIMETO@",
    }
    return tags[tag_name]


_DATETIME_FORMATS = {
    "datetime": "%Y%m%dT%H%M%S",
    "time": "%H%M%S",
    "date": "%Y%m%d",
}


def get_datetime_format(format_type: str) -> str:
    """
    Get the datetime format string for a given format type.

    Parameters
    ----------
    format_type : str
        One of "datetime", "time", or "date"

    Returns
    -------
    str
        The format string for the specified type

    Raises
    ------
    ValueError
        If format_type is not one of the supported types
    """
    if format_type not in _DATETIME_FORMATS:
        raise ValueError(f"Invalid format type: {format_type}. Must be one of {list(_DATETIME_FORMATS.keys())}")
    return _DATETIME_FORMATS[format_type]

