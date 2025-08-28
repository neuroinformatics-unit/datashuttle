def get_project_created_message_template() -> str:
    """Return message template for the project message that shows up on TUI after creating a project."""
    message_template = (
        "A datashuttle project has now been created.\n\n "
        "Next, setup the {method_name} connection. Once complete, navigate to the "
        "'Main Menu' and proceed to the project page, where you will be "
        "able to create and transfer project folders."
    )

    return message_template
