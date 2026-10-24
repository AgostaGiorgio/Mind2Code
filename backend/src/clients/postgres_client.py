from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager


class PostgresClient:
    def __init__(self, db_url: str):
        engine = create_async_engine(db_url, echo=False)
        self.__async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def async_session(self) -> AsyncSession:  # type: ignore
        async with self.__async_session() as session:
            yield session
