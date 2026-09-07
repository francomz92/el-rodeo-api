from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WebhookResponse(BaseModel):
    id: UUID
    url: str
    subscribed_events: list[str]
    is_active: bool
    failure_count: int

    model_config = ConfigDict(from_attributes=True)
