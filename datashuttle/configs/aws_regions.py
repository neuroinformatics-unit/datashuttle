from typing import Dict, List

# -----------------------------------------------------------------------------
# AWS regions
# -----------------------------------------------------------------------------

# These function are used for type checking and providing intellisense to the developer


def get_aws_regions() -> Dict[str, str]:
    aws_regions = {
        "US_EAST_1": "us-east-1",
        "US_EAST_2": "us-east-2",
        "US_WEST_1": "us-west-1",
        "US_WEST_2": "us-west-2",
        "CA_CENTRAL_1": "ca-central-1",
        "EU_WEST_1": "eu-west-1",
        "EU_WEST_2": "eu-west-2",
        "EU_WEST_3": "eu-west-3",
        "EU_NORTH_1": "eu-north-1",
        "EU_SOUTH_1": "eu-south-1",
        "EU_CENTRAL_1": "eu-central-1",
        "AP_SOUTHEAST_1": "ap-southeast-1",
        "AP_SOUTHEAST_2": "ap-southeast-2",
        "AP_NORTHEAST_1": "ap-northeast-1",
        "AP_NORTHEAST_2": "ap-northeast-2",
        "AP_NORTHEAST_3": "ap-northeast-3",
        "AP_SOUTH_1": "ap-south-1",
        "AP_EAST_1": "ap-east-1",
        "SA_EAST_1": "sa-east-1",
        "IL_CENTRAL_1": "il-central-1",
        "ME_SOUTH_1": "me-south-1",
        "AF_SOUTH_1": "af-south-1",
        "CN_NORTH_1": "cn-north-1",
        "CN_NORTHWEST_1": "cn-northwest-1",
        "US_GOV_EAST_1": "us-gov-east-1",
        "US_GOV_WEST_1": "us-gov-west-1",
    }
    return aws_regions


def get_aws_regions_list() -> List[str]:
    return list(get_aws_regions().values())


AWS_REGIONS_DICT = get_aws_regions()  # runtime constant


class AWS_REGION:
    """
    A class to represent AWS regions as constants.
    It is used to provide intellisense for AWS regions in IDEs.
    """

    US_EAST_1 = AWS_REGIONS_DICT["US_EAST_1"]
    US_EAST_2 = AWS_REGIONS_DICT["US_EAST_2"]
    US_WEST_1 = AWS_REGIONS_DICT["US_WEST_1"]
    US_WEST_2 = AWS_REGIONS_DICT["US_WEST_2"]
    CA_CENTRAL_1 = AWS_REGIONS_DICT["CA_CENTRAL_1"]
    EU_WEST_1 = AWS_REGIONS_DICT["EU_WEST_1"]
    EU_WEST_2 = AWS_REGIONS_DICT["EU_WEST_2"]
    EU_WEST_3 = AWS_REGIONS_DICT["EU_WEST_3"]
    EU_NORTH_1 = AWS_REGIONS_DICT["EU_NORTH_1"]
    EU_SOUTH_1 = AWS_REGIONS_DICT["EU_SOUTH_1"]
    EU_CENTRAL_1 = AWS_REGIONS_DICT["EU_CENTRAL_1"]
    AP_SOUTHEAST_1 = AWS_REGIONS_DICT["AP_SOUTHEAST_1"]
    AP_SOUTHEAST_2 = AWS_REGIONS_DICT["AP_SOUTHEAST_2"]
    AP_NORTHEAST_1 = AWS_REGIONS_DICT["AP_NORTHEAST_1"]
    AP_NORTHEAST_2 = AWS_REGIONS_DICT["AP_NORTHEAST_2"]
    AP_NORTHEAST_3 = AWS_REGIONS_DICT["AP_NORTHEAST_3"]
    AP_SOUTH_1 = AWS_REGIONS_DICT["AP_SOUTH_1"]
    AP_EAST_1 = AWS_REGIONS_DICT["AP_EAST_1"]
    SA_EAST_1 = AWS_REGIONS_DICT["SA_EAST_1"]
    IL_CENTRAL_1 = AWS_REGIONS_DICT["IL_CENTRAL_1"]
    ME_SOUTH_1 = AWS_REGIONS_DICT["ME_SOUTH_1"]
    AF_SOUTH_1 = AWS_REGIONS_DICT["AF_SOUTH_1"]
    CN_NORTH_1 = AWS_REGIONS_DICT["CN_NORTH_1"]
    CN_NORTHWEST_1 = AWS_REGIONS_DICT["CN_NORTHWEST_1"]
    US_GOV_EAST_1 = AWS_REGIONS_DICT["US_GOV_EAST_1"]
    US_GOV_WEST_1 = AWS_REGIONS_DICT["US_GOV_WEST_1"]

    @classmethod
    def get_all_regions(cls):
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("__") and isinstance(value, str)
        ]
