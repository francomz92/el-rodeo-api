from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    name: str
    enabled: bool = True
