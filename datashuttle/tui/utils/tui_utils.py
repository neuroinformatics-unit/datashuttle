def get_project_created_message_template() -> str:
    """Return message template for the project message that shows up on TUI after creating a project."""
    message_template = (
        "A datashuttle project has now been created.\n\n "
        "Next, setup the {method_name} connection."
    )

    return message_template
