from enum import Enum


class Sentinel(Enum):
    UNSET = object()

    def __repr__(self):
        return "UNSET"
