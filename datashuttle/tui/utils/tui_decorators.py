from __future__ import annotations

from functools import wraps
from time import monotonic

# -----------------------------------------------------------------------------
# Double-click decorator
# -----------------------------------------------------------------------------


class ClickInfo:
    """
    A class to hold click-info to checking
    double clicks are within the time threshold
    and match the widget id.
    """

    def __init__(self):

        self.prev_click_time = 0.0
        self.prev_click_widget_id = ""


def require_double_click(func):
    """
    A decorator that calls the decorated function
    on a double click, otherwise will not do anything.

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

        if hasattr(event, "input"):
            id = event.input.id
        elif hasattr(event, "node"):
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
