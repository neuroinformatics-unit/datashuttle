## Developer conventions

This page documents existing developer-facing conventions used in the
`datashuttle` codebase. It is intended as a reference for contributors working
on internal implementation details and established coding conventions.

The conventions described here reflect current practices in the codebase.
They are not strict rules, but following them helps improve consistency,
readability, and maintainability.

---

## Terminal user interface (TUI) conventions

When working on the terminal user interface (TUI), contributors should be
mindful of interaction timing and state transitions.

TUI-related code often involves asynchronous updates and delayed rendering.
Designing interactions defensively and allowing sufficient time for UI state
to settle helps avoid fragile behaviour and improves test reliability.

---

## Code organization

As a general convention in the codebase, caller functions are typically defined
above the functions they call. This pattern is not strictly enforced, but
following it improves readability and makes control flow easier to follow.

Related functionality should be grouped logically, with structure driven by
responsibility rather than file size.

---

## Environment and configuration considerations

Some parts of the `datashuttle` codebase depend on external tools and
system-level configuration.

For example:

- Certain workflows rely on external tools such as `rclone`
- Some functionality depends on credentials or environment-specific setup
- Behaviour may vary slightly across operating systems or environments

When introducing new dependencies or environment assumptions, these should be
documented clearly and kept consistent with existing patterns in the codebase.
