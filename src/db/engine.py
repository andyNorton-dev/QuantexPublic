from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.core.config import settings
from db.models import Base

engine = create_async_engine(settings.database_url, echo=False) 
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  
        await conn.run_sync(Base.metadata.create_all)  



if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())

