import copy
import os

from datashuttle import DataShuttle
from datashuttle.utils import aws, utils


def setup_project_for_aws(project: DataShuttle):
    """Update the config file for an AWS connection.

    The connection credentials are fetched from the environment which
    the developer shall set themselves to test locally. In the CI, these
    are set using the github secrets. A random string is added to the
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
    original_get_secret = copy.deepcopy(aws.get_aws_secret_access_key)
    aws.get_aws_secret_access_key = lambda *args, **kwargs: os.environ[
        "AWS_SECRET_ACCESS_KEY"
    ]

    project.setup_aws_connection()

    aws.get_aws_secret_access_key = original_get_secret


def has_aws_environment_variables():
    for key in [
        "AWS_BUCKET_NAME",
        "AWS_ACCESS_KEY_ID",
        "AWS_REGION",
        "AWS_SECRET_ACCESS_KEY",
    ]:
        if key not in os.environ:
            return False

        if os.environ[key].strip() == "":
            return False

    return True
