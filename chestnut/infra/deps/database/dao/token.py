from typing import Dict, Tuple
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from datetime import datetime
from sqlalchemy.sql import select, update, and_
from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker
from sqlalchemy.orm import relationship, Mapped, mapped_column, Mapper

from .base import ChestnutBase
from .....application.user.domain.token import TokenScope, UserToken
from .....application.user.domain.repo import UserTokenRepo


class UserTokenDAO(ChestnutBase):
    __tablename__ = "user_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[bytes] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scope: Mapped[str] = mapped_column()
    create_at: Mapped[datetime] = mapped_column()
    # Relationship
    # Token -*>--1- User
    # many-to -one
    user = relationship("UserDAO")

    __table_args__ = (UniqueConstraint("user_id", "scope", name="ix_user_tokens"),)

    def todomain(self) -> UserToken:
        return UserToken(
            raw_token=self.token,
            user_id=self.user_id,
            scope=TokenScope.fromvalue(self.scope),  # type: ignore
            create_at=self.create_at,
        )


class defaultUserTokenRepo(UserTokenRepo):
    def __init__(
        self,
        session: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session = session

    async def gettokenbyuser(self, user_id: int) -> Dict[str, UserToken]:
        return await super().gettokenbyuser(user_id)

    async def gettokenbyuserandscope(
        self, user_id: int, scope: TokenScope
    ) -> UserToken | None:
        stmt = select(UserTokenDAO).where(
            and_(UserTokenDAO.user_id == user_id, UserTokenDAO.scope == scope.value)
        )

        async with self.session() as session:
            token = await session.scalars(stmt)
            token = token.one_or_none()

        return token.todomain() if isinstance(token, UserToken) else None

    async def addtoken(self, user_token: UserToken) -> Tuple[int, UserToken]:
        async with self.session() as session:
            session.add(user_token)
            await session.commit()

            token = await session.scalars(
                select(UserTokenDAO)
                .where(UserTokenDAO.token == user_token.raw_token)
            )
        
        return token.one_or_none().id, token.one_or_none().todomain()  # type: ignore

    async def removetoken(self, session_id: int) -> None:
        return await super().removetoken(session_id)

    async def removetokenbyuser(self, user_id: int) -> None:
        return await super().removetokenbyuser(user_id)

    async def removetokenbyuserandscope(self, user_id: int, scope: TokenScope) -> None:
        return await super().removetokenbyuserandscope(user_id, scope)
    
    async def updatesametoken(self, user_id: int, scope: TokenScope) -> None:
        current = datetime.utcnow()

        stmt = update(UserTokenDAO).where(and_(
            UserTokenDAO.id == user_id,
            UserTokenDAO.scope == scope.value
        )).values(create_at=current)
        async with self.session() as session:
            await session.execute(stmt)
