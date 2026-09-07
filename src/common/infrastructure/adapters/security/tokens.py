from datetime import timedelta
from uuid import UUID, uuid4

import jwt as pyjwt

from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.entities import RefreshTokenEntity
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.common.infrastructure.core import settings
from src.common.utils.date_utils import get_current_datetime


class TokenService(ITokenService):
    def __init__(self, secret: str, algorithm: str) -> None:
        self.secret = secret
        self.algorithm = algorithm

    # ── Base methods ──────────────────────────────────────────────────────────

    def generate(self, data: dict, exp_minutes: int) -> str:
        payload = data.copy()
        current_datetime = get_current_datetime()
        expire_datetime = current_datetime + timedelta(minutes=exp_minutes)
        payload.update(
            {
                "jti": str(uuid4()),
                "type": "access",
                "exp": expire_datetime,
                "iat": current_datetime,
            }
        )
        return pyjwt.encode(payload, self.secret, self.algorithm)

    def decode(self, token: str):
        try:
            return pyjwt.decode(token, self.secret, [self.algorithm])
        except pyjwt.ExpiredSignatureError:
            raise InvalidCredentialError("Expired token")
        except pyjwt.InvalidTokenError:
            raise InvalidCredentialError("Invalid token")

    # ── Refresh token methods ─────────────────────────────────────────────────

    def generate_refresh_token(
        self,
        user_id: str,
        family_id: str | None = None,
        tenant_id: str | None = None,
    ) -> str:
        """Generate a refresh token JWT with type='refresh' and 7-day expiry.

        The token carries a `refresh_token_id` claim that matches the database
        entity's primary key, enabling direct DB lookup without bcrypt hashing.
        When tenant_id is provided, it is included for token rotation support.
        """
        current_datetime = get_current_datetime()
        expire_datetime = current_datetime + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token_id = uuid4()
        payload: dict = {
            "user_id": user_id,
            "type": "refresh",
            "jti": str(token_id),
            "refresh_token_id": str(token_id),
            "family_id": family_id or str(uuid4()),
            "exp": expire_datetime,
            "iat": current_datetime,
        }
        if tenant_id is not None:
            payload["tenant_id"] = tenant_id
        return pyjwt.encode(payload, self.secret, self.algorithm)

    def decode_refresh_token(self, token: str) -> dict:
        """Decode and validate a refresh token.

        Raises InvalidCredentialError if:
        - The token is expired
        - The token is malformed
        - The token type is not 'refresh'
        """
        try:
            payload = pyjwt.decode(token, self.secret, [self.algorithm])
        except pyjwt.ExpiredSignatureError:
            raise InvalidCredentialError("refresh_token_expired")
        except pyjwt.InvalidTokenError:
            raise InvalidCredentialError("invalid_refresh_token")

        if payload.get("type") != "refresh":
            raise InvalidCredentialError("invalid_refresh_token")

        return payload

    async def rotate_refresh_token(
        self,
        old_token: str,
        repo: IRefreshTokenRepository,
    ) -> tuple[str, str]:
        """Rotate an old refresh token.

        Flow:
        1. Decode old token → get user_id, family_id, refresh_token_id
        2. Look up token in DB by refresh_token_id
        3. If token is already revoked → revoke entire family (reuse detection)
        4. If token is active → revoke it, create new pair in same family
        5. Persist new token entity

        Returns (access_token, new_refresh_token) strings.
        Raises InvalidCredentialError with 'token_family_revoked' on reuse.
        """
        payload = self.decode_refresh_token(old_token)
        user_id: str = payload["user_id"]
        family_id_str: str = payload["family_id"]
        refresh_token_id_str: str = payload.get("refresh_token_id", payload["jti"])
        family_id = UUID(family_id_str)
        token_id = UUID(refresh_token_id_str)

        # Look up token in DB
        stored_entity = await repo.find_by_id(token_id)

        if stored_entity and stored_entity.is_revoked:
            # Reuse detection: this token was already rotated
            await repo.revoke_family(family_id)
            raise InvalidCredentialError("token_family_revoked")

        # Generate new token pair with tenant context
        token_payload: dict = {"user_id": user_id}
        if "tenant_id" in payload:
            token_payload["tenant_id"] = payload["tenant_id"]
        access_token = self.generate(
            token_payload,
            exp_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        new_refresh_token = self.generate_refresh_token(
            user_id=user_id,
            family_id=family_id_str,
            tenant_id=payload.get("tenant_id"),
        )

        # Decode new refresh to get its token_id for storage
        new_payload = self.decode_refresh_token(new_refresh_token)
        new_token_id_str: str = new_payload.get("refresh_token_id", new_payload["jti"])

        # Revoke old token in DB
        if stored_entity:
            await repo.revoke_token(stored_entity)

        # Persist new token entity
        new_entity = RefreshTokenEntity(
            id=UUID(new_token_id_str),
            user_id=UUID(user_id),
            token_hash=new_token_id_str,  # use token ID as unique hash (ID-based lookup)
            family_id=family_id,
            expires_at=get_current_datetime() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
        await repo.save(new_entity)

        return access_token, new_refresh_token

    async def revoke_refresh_token(
        self,
        token: str,
        repo: IRefreshTokenRepository,
    ) -> None:
        """Revoke a specific refresh token by decoding it and looking up its ID."""
        payload = self.decode_refresh_token(token)
        refresh_token_id_str: str = payload.get("refresh_token_id", payload["jti"])
        token_id = UUID(refresh_token_id_str)

        stored_entity = await repo.find_by_id(token_id)
        if stored_entity:
            await repo.revoke_token(stored_entity)

    def generate_ws_token(self, user_id: str, tenant_id: str | None = None) -> str:
        current_datetime = get_current_datetime()
        expire_datetime = current_datetime + timedelta(minutes=settings.WS_TOKEN_EXPIRE_MINUTES)
        payload: dict = {
            "user_id": user_id,
            "type": "ws",
            "purpose": "websocket",
            "jti": str(uuid4()),
            "exp": expire_datetime,
            "iat": current_datetime,
        }
        if tenant_id is not None:
            payload["tenant_id"] = tenant_id
        return pyjwt.encode(payload, self.secret, self.algorithm)

    async def revoke_user_refresh_tokens(
        self,
        user_id: UUID,
        repo: IRefreshTokenRepository,
    ) -> None:
        """Revoke ALL refresh tokens for the given user."""
        await repo.revoke_all_user_tokens(user_id)
