from pydantic import BaseModel, HttpUrl


class WebhookCreate(BaseModel):
    url: HttpUrl
    subscribed_events: list[str]


class WebhookUpdate(BaseModel):
    url: HttpUrl | None = None
    subscribed_events: list[str] | None = None
    is_active: bool | None = None
