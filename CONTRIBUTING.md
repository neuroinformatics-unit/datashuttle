# Contributing to datashuttle

Thank you for your interest in contributing to `datashuttle`!
We welcome bug reports, documentation improvements, feature requests, and code
contributions.

This guide focuses on repository-specific contribution practices. General
contribution guidelines are also defined at the Neuroinformatics Unit
organization level and apply here as well.

---

## Getting started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your work

```bash
git checkout -b my-feature
```
## Development setup
We recommend using a virtual environment.
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
Install the project in editable mode:
```bash
pip install -e .
```
## Running tests locally
We strongly encourage contributors to run the test suite locally before opening
a pull request. This helps catch issues early and makes development and review
faster.

## Installing test dependencies
Install the project in editable mode with test dependencies:
```bash 
pip install -e .[test]
```
Ensure pytest is available:
```bash
pip install pytest
```
## Running the full test suite
From the root of the repository, run:
```bash
pytest
```
This runs all tests that can be executed in a local development environment.
## Running a subset of tests
Run a specific test file:
```bash
pytest tests/test_validation.py
```
Run tests matching a keyword:
```bash
pytest -k validate
```
## Tests requiring additional infrastructure
Some tests depend on external services and may be skipped automatically when run
locally:
- SSH-related tests may require Docker to simulate remote hosts
- Cloud storage tests (Google Drive, AWS) require credentials and are not
expected to run from forks
- Backward compatibility tests may rely on historical data layouts
These tests are primarily exercised through the project’s GitHub Actions
workflows. Skipped tests in a local environment are expected and do not indicate
a failure.
## Code style and quality
The project uses automated formatting and linting via pre-commit.
Before opening a pull request, please ensure:
```bash
pre-commit run --all-files
```
## Submitting a pull request
- Keep pull requests focused and scoped
- Add tests where appropriate
- Update documentation when behavior changes
- Reference relevant issues in the PR description
All pull requests are reviewed by maintainers before merging.

Thank you for helping improve datashuttle!