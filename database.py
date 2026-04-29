import aiosqlite
from datetime import datetime
from typing import Optional, List

DB_PATH = "planner.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def add_event(
    user_id: int,
    title: str,
    description: Optional[str],
    event_date: str,
    event_time: str
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO events (user_id, title, description, event_date, event_time)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, description, event_date, event_time)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_events(user_id: int) -> List[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE user_id = ? ORDER BY event_date, event_time",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_event(user_id: int, event_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM events WHERE user_id = ? AND id = ?",
            (user_id, event_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_event(user_id: int, event_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM events WHERE user_id = ? AND id = ?",
            (user_id, event_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
