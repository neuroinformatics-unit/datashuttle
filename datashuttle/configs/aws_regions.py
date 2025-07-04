from typing import List, Literal, get_args

# -----------------------------------------------------------------------------
# AWS regions
# -----------------------------------------------------------------------------

AwsRegion = Literal[
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-north-1",
    "eu-south-1",
    "eu-central-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-south-1",
    "ap-east-1",
    "sa-east-1",
    "il-central-1",
    "me-south-1",
    "af-south-1",
    "cn-north-1",
    "cn-northwest-1",
    "us-gov-east-1",
    "us-gov-west-1",
]


def get_aws_regions_list() -> List[str]:
    """Return AWS S3 bucket regions as a list."""
    return list(get_args(AwsRegion))
