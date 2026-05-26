from enum import Enum, StrEnum


class Sentinel(Enum):
    UNSET = "unset"

    def __repr__(self):
        return "UNSET"


class EnvironmentType(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
