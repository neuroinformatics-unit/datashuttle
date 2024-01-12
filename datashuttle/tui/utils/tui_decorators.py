from __future__ import annotations

from functools import wraps
from time import monotonic

# -----------------------------------------------------------------------------
# Double-click decorator
# -----------------------------------------------------------------------------


def require_double_click(func):
    """
    A decorator that calls the decorated function
    on a double click, otherwise will not do anything.

    Requires the first argument (`self` on the class) to
    have the attribute `prev_click_time`).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        parent_class = args[0]

        assert hasattr(parent_class, "prev_click_time"), (
            "Decorator must be used on class method where the class as "
            "the attribute `prev_click_time`."
        )

        click_time = monotonic()

        if click_time - parent_class.prev_click_time < 0.5:
            parent_class.prev_click_time = click_time
            return func(*args, **kwargs)

        parent_class.prev_click_time = click_time

    return wrapper
