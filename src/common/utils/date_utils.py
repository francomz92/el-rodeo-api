from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def get_current_datetime() -> datetime:
    return datetime.now(timezone.utc)


def get_local_from_utc(datetime: datetime, tz_name: str = "America/Argentina/Buenos_Aires") -> datetime:
    return datetime.astimezone(ZoneInfo(tz_name))
