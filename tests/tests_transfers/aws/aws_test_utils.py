import copy
import os

from datashuttle import DataShuttle
from datashuttle.utils import aws


def setup_project_for_aws(project: DataShuttle):
    aws_bucket_name = os.environ["AWS_BUCKET_NAME"]
    project.update_config_file(
        connection_method="aws",
        central_path=f"{aws_bucket_name}/main/{project.project_name}",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_region=os.environ["AWS_REGION"],
    )


def setup_aws_connection(project: DataShuttle):
    """
    Convenience function to set up the AWS connection by
    mocking the `aws.get_aws_secret_access_key` function.
    """
    original_get_secret = copy.deepcopy(aws.get_aws_secret_access_key)
    aws.get_aws_secret_access_key = lambda *args, **kwargs: os.environ[
        "AWS_SECRET_ACCESS_KEY"
    ]

    project.setup_aws_connection()

    aws.get_aws_secret_access_key = original_get_secret
