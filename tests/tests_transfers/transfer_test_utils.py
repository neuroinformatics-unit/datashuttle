import os

from dotenv import load_dotenv


def check_if_env_vars_are_loaded(required_variables):
    """Check if environment variables required to run tests are loaded.

    If we are on GitHub, these should be loaded in the
    workflow `.yaml` files. Otherwise, these can be set manually
    or (more conveniently) added to a `.env` file in the project root.

    Parameters
    ----------
    required_variables :
        A list of required variables to check for.

    Returns
    -------
    bool
        True if all required environment variables are loaded, False otherwise.
    """
    # Outside of GitHub actions, if env vars are not
    # loaded try and load using dotenv.
    if not os.getenv("GITHUB_ACTIONS"):
        if not all([var in os.environ for var in required_variables]):
            if not load_dotenv():
                return False

    for var in required_variables:
        if var not in os.environ:
            return False

        # On CI triggered by forked repositories, secrets are empty
        if os.environ[var].strip() == "":
            return False

    return True
