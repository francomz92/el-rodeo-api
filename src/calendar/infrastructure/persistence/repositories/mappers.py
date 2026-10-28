"""Row-to-entity builders for the calendar repositories."""

from sqlalchemy import RowMapping

from src.calendar.domain.entities.calendar_event_entity import CalendarEventEntity


def build_calendar_event(data: RowMapping) -> CalendarEventEntity:
    """Build a CalendarEventEntity from a SQLAlchemy RowMapping."""
    return CalendarEventEntity(
        id=data["id"],
        tenant_id=data["tenant_id"],
        user_id=data["user_id"],
        created_at=data["created_at"],
        title=data["title"],
        description=data["description"],
        start=data["start"],
        end=data["end"],
        pending=data["pending"],
        type=data["type"],
        participants=[],
        participant_user_ids=data["participant_user_ids"] or [],
    )
