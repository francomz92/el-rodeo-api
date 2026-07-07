from dataclasses import dataclass


@dataclass(frozen=True)
class Quota:
    name: str
    limit: int
    description: str = ""
