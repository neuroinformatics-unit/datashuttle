# Contributing Guide

**Contributors to datashuttle are absolutely encouraged**, whether to fix a bug or develop a new feature.

If you're unsure about any part of the contributing process or have any questions, please
get in touch through our [Zulip chat](https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle).
Otherwise, feel free to dive right in and start contributing by
[creating a development environment](#creating-a-development-environment)
and [opening a pull request](#pull-requests).

The core development team will support you in contributing code, regardless of your experience!

## Creating a development environment

For detailed instructions on installing ``datashuttle`` along with
all necessary packages for development, refer to the `Developers` tab on the
[How to install ``datashuttle``](how-to-install) page.

Briefly, after installing Rclone, the ``datashuttle`` repository can be cloned:

```sh
git clone git@github.com:neuroinformatics-unit/datashuttle.git
```

and ``datashuttle`` pip-installed with the developer tag:


```sh
pip install -e .[dev]
```

or if using `zsh`:

```sh
pip install -e '.[dev]'
```

Finally, initialise the [pre-commit hooks](#formatting-and-pre-commit-hooks):

```bash
pre-commit install
```


## Pull requests

In all cases, please submit code to the main repository via a pull request. The developers recommend and adhere
to the following conventions:

- Please submit *draft* pull requests as early as possible (you can still push to the branch once submitted) to
  allow for discussion.
- One approval of a PR (by a repo maintainer) is sufficient for it to be merged.
- If the PR receives approval without additional comments, it will be merged immediately by the approving reviewer.


A typical PR workflow would be as follows:
* Create a new branch, make your changes, and add them with `git add`.
* When you attempt to commit, the [pre-commit hooks](#formatting-and-pre-commit-hooks) will be triggered.
* `git add` any changes made by the hooks, and commit. More information on dealing with the [pre-commit hooks](#formatting-and-pre-commit-hooks) is available below.
* Push your changes to GitHub and open a draft pull request.
* Please don't hesitate to ask any developer for help on draft pull requests at our [Zulip chat](https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle).
* If all checks run successfully, mark the pull request as ready for review.
* Respond to review comments and implement any requested changes.
* One of the maintainers will approve the PR.
* Your PR will be (squash-)merged into the *main* branch!

When submitting a PR, it is helpful to consider how the new
features will be tested. If you are familiar with testing, please
try to add tests for new functionality. However if you're not, no problem!
We're happy to help with both the design and implementation of tests so please
don't let this discourage you from opening a PR. We take a similar approach to
[documenting new features](#contributing-documentation), which is discussed further below.

## Formatting and pre-commit hooks

Running `pre-commit install` will set up [pre-commit hooks](https://pre-commit.com/) to ensure a consistent formatting style. Currently, these include:
* [ruff](https://github.com/astral-sh/ruff), which does a number of jobs including code linting and auto-formatting.
* [mypy](https://mypy.readthedocs.io/en/stable/index.html), a static type checker.
* [check-manifest](https://github.com/mgedmin/check-manifest), to ensure that the right files are included in the pip package.
* [codespell](https://github.com/codespell-project/codespell), to check for common misspellings.


Pre-commit hooks will automatically run when a commit is made.
To manually run all the hooks before committing:

```sh
pre-commit run     # for staged files
pre-commit run -a  # for all files in the repository
```

Some problems will be automatically fixed by the hooks. In this case, you should
stage the auto-fixed changes and run the hooks again:

```sh
git add .
pre-commit run
```

If a problem cannot be auto-fixed, the corresponding tool will provide
information on what the issue is and how to fix it. For example, `ruff` might
output something like:

```sh
datashuttle.py:551:80: E501 Line too long (90 > 79)
```

This pinpoints the problem to a single line of code and a specific [ruff rule](https://docs.astral.sh/ruff/rules/) violation.
Sometimes you may have good reasons to ignore a particular rule for a specific line.
You can do this by adding an inline comment, e.g. `# noqa: E501`. Replace `E501` with the code of the rule you want to ignore.

Don't worry if you are stuck and are not sure how to fix linting
issues. Feel free to commit with the `--no-verify` option which will
skip pre-commit checks, and ask for help in your PR.

For docstrings, we adhere to the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) style.
Make sure to provide docstrings for all public functions, classes, and methods.

## Running tests locally

Unit and integration tests are important tools to ensure code is working as expected,
and to protect against future changes breaking existing functionality. 

All tests are automatically run on GitHub actions for open PRs. However, it can be useful
to run tests locally to ensure everything is working on your system. We use `pytest` to 
manage running `datashuttle` tests.

### Installing test dependencies

All dependencies required for testing are included in the `[dev]` section of
the `pyproject.toml`. To install these dependencies, install the package with
the following command, run in the project root directory:
```bash
pip install -e .[dev]
```

Note that on `zsh` shell, you may need to format this as:

```bash
pip install -e ".[dev]"
```

### Running the full test suite

From the root of the repository, run:
```bash
pytest
```
This runs all tests that can be executed in a local development environment.

To run a specific test file, you can run:

```bash
pytest tests/test_validation.py
```

or to run any tests matching a keyword:

```bash
pytest -k validate
```

### Tests requiring additional infrastructure

Some tests depend on external infrastructure and will be skipped automatically 
when run locally:

- To run tests of SSH transfer, Docker must be installed and running. 
- Cloud storage tests (Google Drive, AWS) require private credentials to run
and are generally not expected to be run outside the GitHub actions environment. Please
contact the development team if you require local testing of Google Drive or AWS for your contribution. 

## Contributing documentation

It is very important that the documentation for ``datashuttle`` is clear,
accurate and concise. A key principle of ``datashuttle`` is it should
make data acquisition simple and easy—therefore it should be
well-documented.

For these reasons every part of all software must be documented as
thoroughly as possible, and all new features must be fully documented. If you
notice any areas where the documentation can be improved, please don't hesitate
to make a contribution.



### Working with the documentation

The documentation is found in the `docs/source` folder, where the structure mirrors the rendered website.

Dependencies for building the documentation locally can be found at `docs/requirements.txt`.
To install these, change directory to the `docs` folder in your terminal and type:

```
pip install -r requirements.txt
```

The command to build the documentation is then:

```
sphinx-build source build
```

The documentation will be built and output to the `build` folder. To
read the built documentation in a browser, navigate to the `build`
folder and open the `index.html` file.


### Editing the documentation

The documentation is hosted using [GitHub Pages](https://pages.github.com/), and the source can be found at
[GitHub](https://github.com/neuroinformatics-unit/datashuttle/tree/main/docs).
Most content is found under `docs/source`, where the structure mirrors the rendered website.

To edit a page, please:

- Fork the repository
- Make edits to the relevant pages
- Build the pages as above to inspect your changes
- Create a pull request outlining the changes made

If you aren't sure where the changes should be made, please
[get in touch!](https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle)


### Previewing the documentation in continuous integration

We use [artifact.ci](https://artifact.ci/) to preview the documentation that is built as part of our GitHub Actions workflow. To do so:
1. Go to the "Checks" tab in the GitHub PR.
2. Click on the "Docs" section on the left.
3. If the "Build Sphinx Docs" action is successful, a summary section will appear under the block diagram with a link to preview the built documentation.
4. Click on the link and wait for the files to be uploaded (it may take a while the first time). You may be asked to sign in to GitHub.
5. Once the upload is complete, look for `docs/build/html/index.html` under the "Detected Entrypoints" section.
