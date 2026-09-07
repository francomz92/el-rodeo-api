from dataclasses import dataclass


@dataclass(frozen=True)
class QuotaEntity:
    name: str
    limit: int
    description: str = ""
