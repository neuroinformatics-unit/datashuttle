import copy
import os

from datashuttle import DataShuttle
from datashuttle.utils import aws, utils

from .. import transfer_test_utils


def setup_project_for_aws(project: DataShuttle):
    """Update the config file for an AWS connection.

    The connection credentials are fetched from the environment which
    the developer shall set themselves to test locally. In the CI, these
    are set using the GitHub secrets. A random string is added to the
    central path so that the test project paths do not interfere while
    running multiple test instances simultaneously in CI.
    """
    aws_bucket_name = os.environ["AWS_BUCKET_NAME"]

    random_string = utils.get_random_string()

    project.update_config_file(
        connection_method="aws",
        central_path=f"{aws_bucket_name}/{random_string}/{project.project_name}",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_region=os.environ["AWS_REGION"],
    )


def setup_aws_connection(project: DataShuttle):
    """
    Convenience function to set up the AWS connection by
    mocking the `aws.get_aws_secret_access_key` function.

    The `AWS_SECRET_ACCESS_KEY` is set in the environment by the CI while
    testing. For testing locally, the developer must set it themselves.
    """

    def mock_input(_: str) -> str:
        return "y"

    import builtins

    original_input = copy.deepcopy(builtins.input)
    builtins.input = mock_input  # type: ignore

    original_get_secret = copy.deepcopy(aws.get_aws_secret_access_key)

    aws.get_aws_secret_access_key = lambda *args, **kwargs: os.environ[
        "AWS_SECRET_ACCESS_KEY"
    ]

    project.setup_aws_connection()

    builtins.input = original_input
    aws.get_aws_secret_access_key = original_get_secret


def has_aws_environment_variables():
    """Check for environment variables needed to run AWS tests.

    Environment variables can be stored in a `.env` file in the
    project root, for use with `python-dotenv`. Otherwise,
    they are set up in GitHub actions.
    """
    required_variables = [
        "AWS_BUCKET_NAME",
        "AWS_ACCESS_KEY_ID",
        "AWS_REGION",
        "AWS_SECRET_ACCESS_KEY",
    ]

    return transfer_test_utils.check_if_env_vars_are_loaded(required_variables)
