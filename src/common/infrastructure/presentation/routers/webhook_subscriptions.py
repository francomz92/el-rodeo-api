"""RESTful CRUD for tenant-scoped WebhookSubscription management.

Endpoints under ``/webhooks`` allow authenticated tenants to register,
list, update, and delete webhook subscriptions.  The HMAC signing secret
is auto-generated on creation and never returned in full after creation.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.common.infrastructure.adapters.http.input.webhook_schemas import (
    WebhookCreate,
    WebhookUpdate,
)
from src.common.infrastructure.adapters.http.output.webhook_schemas import (
    WebhookResponse,
)
from src.common.infrastructure.presentation.dependencies.webhooks import (
    GetWebhookSubscriptionService,
)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
    dependencies=[is_authenticated_current_user],
)


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    current_user: GetCurrentUser,
    service: GetWebhookSubscriptionService,
) -> WebhookResponse:
    """Register a new webhook subscription for the current tenant."""
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")
    sub = await service.create(
        tenant_id=current_user.tenant_id,
        url=data.url,
        subscribed_events=data.subscribed_events,
    )
    return WebhookResponse.model_validate(sub)


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: GetCurrentUser,
    service: GetWebhookSubscriptionService,
) -> list[WebhookResponse]:
    """List all webhook subscriptions for the current tenant."""
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")
    subs = await service.list_for_tenant(tenant_id=current_user.tenant_id)
    return [WebhookResponse.model_validate(s) for s in subs]


@router.get("/{subscription_id}", response_model=WebhookResponse)
async def get_webhook(
    subscription_id: UUID,
    current_user: GetCurrentUser,
    service: GetWebhookSubscriptionService,
) -> WebhookResponse:
    """Get a single webhook subscription by ID (tenant-scoped)."""
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")
    sub = await service.get_by_id_for_tenant(
        subscription_id=subscription_id,
        tenant_id=current_user.tenant_id,
    )
    return WebhookResponse.model_validate(sub)


@router.put("/{subscription_id}", response_model=WebhookResponse)
async def update_webhook(
    subscription_id: UUID,
    data: WebhookUpdate,
    current_user: GetCurrentUser,
    service: GetWebhookSubscriptionService,
) -> WebhookResponse:
    """Update a webhook subscription's URL, events, or active status."""
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")
    sub = await service.update(
        subscription_id=subscription_id,
        tenant_id=current_user.tenant_id,
        url=data.url,
        subscribed_events=data.subscribed_events,
        is_active=data.is_active,
    )
    return WebhookResponse.model_validate(sub)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    subscription_id: UUID,
    current_user: GetCurrentUser,
    service: GetWebhookSubscriptionService,
) -> None:
    """Delete a webhook subscription by ID (tenant-scoped)."""
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")
    await service.delete(
        subscription_id=subscription_id,
        tenant_id=current_user.tenant_id,
    )
