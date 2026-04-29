import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def init(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                guild_id BIGINT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
            """)

    async def get_last_application(self, user_id: int, guild_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
            SELECT * FROM applications
            WHERE user_id=$1 AND guild_id=$2
            ORDER BY created_at DESC
            LIMIT 1
            """, user_id, guild_id)

    async def create_application(self, user_id: int, guild_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
            INSERT INTO applications(user_id, guild_id)
            VALUES($1, $2)
            RETURNING id
            """, user_id, guild_id)

    async def update_status(self, app_id: int, status: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
            UPDATE applications SET status=$1 WHERE id=$2
            """, status, app_id)


db = Database()
