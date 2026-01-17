from sqlalchemy import text
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def create_db():
    # Connect to 'postgres' default DB to create our target DB
    default_db_url = settings.DATABASE_URL.rsplit('/', 1)[0] + "/postgres"
    engine = create_async_engine(default_db_url, isolation_level="AUTOCOMMIT")
    
    target_db_name = settings.DATABASE_URL.rsplit('/', 1)[1]

    async with engine.connect() as conn:
        # Check if DB exists
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{target_db_name}'")
        )
        if not result.scalar():
            print(f"Creating database: {target_db_name}")
            await conn.execute(text(f"CREATE DATABASE {target_db_name}"))
        else:
            print(f"Database {target_db_name} already exists.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_db())
