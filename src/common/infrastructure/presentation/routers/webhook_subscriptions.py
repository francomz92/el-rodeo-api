"""RESTful CRUD for tenant-scoped WebhookSubscription management.

Endpoints under ``/webhooks`` allow authenticated tenants to register,
list, update, and delete webhook subscriptions.  The HMAC signing secret
is auto-generated on creation and never returned in full after creation.
"""

from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.common.infrastructure.persistence.models.webhook_subscription import (
    WebhookSubscription,
)
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
    dependencies=[is_authenticated_current_user],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────


class WebhookCreate(BaseModel):
    """Request schema for creating a webhook subscription."""

    url: str
    subscribed_events: list[str]


class WebhookUpdate(BaseModel):
    """Request schema for updating a webhook subscription."""

    url: str | None = None
    subscribed_events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    """Response schema for a webhook subscription."""

    id: UUID
    url: str
    subscribed_events: list[str]
    is_active: bool
    failure_count: int


# ── Helpers ───────────────────────────────────────────────────────────────


def _generate_secret() -> str:
    """Generate a random HMAC signing secret (32 bytes, URL-safe base64)."""
    return secrets.token_urlsafe(32)


async def _get_subscription_or_404(
    uow: GetUnitOfWork,
    tenant_id: UUID,
    subscription_id: UUID,
) -> WebhookSubscription:
    """Fetch a webhook subscription by id, ensuring tenant ownership.

    Raises HTTPException(404) if not found or not owned by the tenant.
    """
    stmt = select(WebhookSubscription).where(
        WebhookSubscription.id == subscription_id,
        WebhookSubscription.tenant_id == tenant_id,
    )
    result = await uow.db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook subscription not found",
        )
    return sub


def _to_response(sub: WebhookSubscription) -> WebhookResponse:
    return WebhookResponse(
        id=sub.id,
        url=sub.url,
        subscribed_events=list(sub.subscribed_events),
        is_active=sub.is_active,
        failure_count=sub.failure_count,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    current_user: GetCurrentUser,
    uow: GetUnitOfWork,
) -> WebhookResponse:
    """Register a new webhook subscription for the current tenant.

    The HMAC signing secret is auto-generated. The subscription starts
    active and will receive events matching *subscribed_events*.
    """
    assert current_user.tenant_id is not None
    sub = WebhookSubscription(
        tenant_id=current_user.tenant_id,
        url=data.url,
        secret=_generate_secret(),
        subscribed_events=data.subscribed_events,
    )
    uow.db.add(sub)
    await uow.commit()
    await uow.refresh(sub)
    return _to_response(sub)


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: GetCurrentUser,
    uow: GetUnitOfWork,
) -> list[WebhookResponse]:
    """List all webhook subscriptions for the current tenant."""
    assert current_user.tenant_id is not None
    stmt = (
        select(WebhookSubscription).where(WebhookSubscription.tenant_id == current_user.tenant_id).order_by(WebhookSubscription.created_at)
    )
    result = await uow.db.execute(stmt)
    subs = result.scalars().all()
    return [_to_response(sub) for sub in subs]


@router.get("/{subscription_id}", response_model=WebhookResponse)
async def get_webhook(
    subscription_id: UUID,
    current_user: GetCurrentUser,
    uow: GetUnitOfWork,
) -> WebhookResponse:
    """Get a single webhook subscription by ID (tenant-scoped)."""
    assert current_user.tenant_id is not None
    sub = await _get_subscription_or_404(uow, current_user.tenant_id, subscription_id)
    return _to_response(sub)


@router.put("/{subscription_id}", response_model=WebhookResponse)
async def update_webhook(
    subscription_id: UUID,
    data: WebhookUpdate,
    current_user: GetCurrentUser,
    uow: GetUnitOfWork,
) -> WebhookResponse:
    """Update a webhook subscription's URL, events, or active status."""
    assert current_user.tenant_id is not None
    sub = await _get_subscription_or_404(uow, current_user.tenant_id, subscription_id)

    if data.url is not None:
        sub.url = data.url
    if data.subscribed_events is not None:
        sub.subscribed_events = data.subscribed_events
    if data.is_active is not None:
        sub.is_active = data.is_active

    await uow.commit()
    await uow.refresh(sub)
    return _to_response(sub)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    subscription_id: UUID,
    current_user: GetCurrentUser,
    uow: GetUnitOfWork,
) -> None:
    """Delete a webhook subscription by ID (tenant-scoped)."""
    assert current_user.tenant_id is not None
    sub = await _get_subscription_or_404(uow, current_user.tenant_id, subscription_id)
    await uow.db.delete(sub)  # type: ignore[misc]
    await uow.commit()
