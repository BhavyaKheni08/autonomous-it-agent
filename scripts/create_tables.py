
import asyncio
from app.core.database import engine
from app.models.sql_models import Base

async def init_tables():
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_tables())
