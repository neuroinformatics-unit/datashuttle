def process_str_for_textual(message: str) -> str:
    """
    From textual v2, "[" in string is interpreted as markdown style syntax.
    These need to be escaped in all strings passed to textual.
    """
    return message.replace("[", "\[")
