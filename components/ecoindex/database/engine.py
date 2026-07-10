from typing import AsyncGenerator

from ecoindex.config import Settings
from ecoindex.models.api import *  # noqa: F401, F403
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

engine = create_async_engine(
    Settings().DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool,
    echo=Settings().DEBUG,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator:
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
