from abc import ABC, abstractmethod


class ITokenBlacklistService(ABC):
    """Interface for blacklisting and verifying revoked tokens.

    When a user logs out, the token's unique ID (jti) is stored in a blacklist
    for the remaining duration of the token's validity. Every authenticated
    request checks this blacklist before accepting the token.
    """

    @abstractmethod
    async def blacklist(self, jti: str, ttl: int) -> None:
        """Mark a token as invalid for the given TTL (in seconds)."""
        raise NotImplementedError

    @abstractmethod
    async def is_blacklisted(self, jti: str) -> bool:
        """Return True if the token has been revoked."""
        raise NotImplementedError
