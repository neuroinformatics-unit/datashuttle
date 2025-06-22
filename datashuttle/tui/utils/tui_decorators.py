from __future__ import annotations

from functools import wraps
from time import monotonic

from textual.widgets import DirectoryTree

from datashuttle.tui.custom_widgets import ClickableInput

# -----------------------------------------------------------------------------
# Double-click decorator
# -----------------------------------------------------------------------------


class ClickInfo:
    """A class to hold click-info.

    This stores click history to allow later checking
    that double clicks occur within a time threshold
    and that the same widget is clicked twice.
    """

    def __init__(self):
        """Initialise the ClickInfo."""
        self.prev_click_time = 0.0
        self.prev_click_widget_id = ""


def require_double_click(func):
    """Call the decorated function on a double click.

    Requires the first argument (`self` on the class) to
    have the attribute `click_info`). Any class holding a widget
    that supports double-clicking must have the attribute
    self.click_info = ClickInfo()

    The first (non-self) argument depends on the decorated function,
    which is usually widget-specific. Unfortunately, these must be
    supported on a case-by-case bases and extended when required.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        parent_class = args[0]

        assert hasattr(parent_class, "click_info"), (
            "Decorator must be used on class method where the class as "
            "the attribute `self.click_info = ClickInfo()`."
        )

        click_time = monotonic()
        event = args[1]

        if isinstance(event, ClickableInput.Clicked):
            id = event.input.id
        elif isinstance(event, DirectoryTree.FileSelected) or isinstance(
            event, DirectoryTree.DirectorySelected
        ):
            id = event.node.tree.id
        else:
            raise RuntimeError(
                "The message type for the widget you are trying to"
                "register clicks on is not supported. Add it to the decorator."
            )

        if (
            click_time - parent_class.click_info.prev_click_time < 0.5
            and id == parent_class.click_info.prev_click_widget_id
        ):
            parent_class.click_info.prev_click_time = click_time
            parent_class.click_info.prev_click_widget_id = id
            return func(*args, **kwargs)

        parent_class.click_info.prev_click_time = click_time
        parent_class.click_info.prev_click_widget_id = id

    return wrapper
