## Developer conventions (work in progress)

This page describes developer-facing conventions and testing behavior used in
the `datashuttle` codebase.

The conventions documented here are **soft conventions** rather than strict
rules. They reflect existing practices in the codebase and are intended to help
contributors understand expectations and avoid common pitfalls.

This documentation is a work in progress and will evolve over time.

  ---

## Testing conventions

### TUI tests

When writing TUI tests, `await pilot.pause()` should be called at the end of the test. This ensures the interface has fully settled before the test exits and helps avoid flaky test behaviour.

---

### Cloud connection tests (SSH, Google Drive, AWS)

Tests related to cloud-based connection methods have the following behavior:

Tests for AWS and Google Drive do not run on forks.

These tests are expected to pass only after a pull request is merged.

Contributors should not attempt to fix these failures within forked CI runs.

These tests rely on rclone configuration, credentials, and infrastructure that are not available in forked environments.

---

### Backward compatibility tests

The test suite includes backward compatibility checks to ensure older configuration formats and workflows continue to function correctly.

When modifying configuration-related code, contributors should be mindful of these tests and expect failures if compatibility is broken.

---

### Code organization

As a general convention in the codebase, caller functions are typically defined above the functions they call. This is not strictly enforced but following this pattern improves readability and consistency.

---

### Environment and configuration notes
Some parts of the codebase depend on external tools and system configuration.

Certain workflows rely on external tools such as rclone.

Some tests require credentials or infrastructure not available in all environments.

Environment-based configuration (for example, .env files) may be adopted in the future and should be documented here if introduced.

---

### Scope and future work

This page serves as an initial location for developer-oriented documentation.

Planned or potential future additions include:

A high-level architecture overview

Detailed documentation of data transfer and rclone interactions

TUI design patterns and conventions

Expanded testing strategy documentation

Contributions and improvements to this documentation are welcome.