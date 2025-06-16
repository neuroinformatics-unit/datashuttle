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


def require_double_click_input_box(func):
    """
    Similar to the `require_double_click` decorator but adds an
    extra check to register a double click.

    Requires the first argument (`self` on the class) to
    have the attribute `prev_click_time` and `prev_click_input_id).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        parent_class = args[0]
        event = args[1]

        assert hasattr(parent_class, "prev_click_time"), (
            "Decorator must be used on class method where the class as "
            "the attribute `prev_click_time`."
        )
        assert hasattr(parent_class, "prev_click_input_id"), (
            "Decorator must be used on class method where the class as "
            "the attribute `prev_click_time`."
        )

        click_time = monotonic()
        input_id = event.input.id

        if (
            click_time - parent_class.prev_click_time < 0.5
            and input_id == parent_class.prev_click_input_id
        ):
            parent_class.prev_click_time = click_time
            parent_class.prev_click_input_id = input_id
            return func(*args, **kwargs)

        parent_class.prev_click_time = click_time
        parent_class.prev_click_input_id = input_id

    return wrapper
