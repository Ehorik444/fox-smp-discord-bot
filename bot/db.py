import asyncpg
import sqlite3
import os
from config import DATABASE_URL

USE_SQLITE = False

if not DATABASE_URL:
    USE_SQLITE = True
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    conn.commit()


pool = None


async def init_db():
    global pool
    if USE_SQLITE:
        return

    pool = await asyncpg.create_pool(DATABASE_URL)


async def create_application(user_id: int, content: str):
    if USE_SQLITE:
        cur.execute(
            "INSERT INTO applications (user_id, content, status, created_at) VALUES (?, ?, ?, datetime('now'))",
            (user_id, content, "pending"),
        )
        conn.commit()
        return

    async with pool.acquire() as con:
        await con.execute(
            "INSERT INTO applications(user_id, content, status) VALUES($1,$2,$3)",
            user_id,
            content,
            "pending",
        )


async def update_status(app_id: int, status: str):
    if USE_SQLITE:
        cur.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))
        conn.commit()
        return

    async with pool.acquire() as con:
        await con.execute(
            "UPDATE applications SET status=$1 WHERE id=$2",
            status,
            app_id,
        )
