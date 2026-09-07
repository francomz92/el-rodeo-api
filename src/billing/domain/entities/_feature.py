from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureEntity:
    name: str
    enabled: bool = True
