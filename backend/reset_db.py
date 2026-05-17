import asyncio
from sqlalchemy import text
from app.database import engine
from app.models.base import Base
from app.models import *


async def reset():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    print("Tables recreated")


asyncio.run(reset())
