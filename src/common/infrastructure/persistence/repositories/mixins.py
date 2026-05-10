from sqlalchemy.ext.asyncio import AsyncSession


class SessionMixin:
    def __init__(self, session: AsyncSession):
        self.db = session
