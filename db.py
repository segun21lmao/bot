import aiosqlite

DB_PATH = "tasks.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER UNIQUE,
                thread_id INTEGER,
                thread_message_id INTEGER UNIQUE,         
                title TEXT,
                description TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_members (
                task_id INTEGER,
                user_id INTEGER,
                UNIQUE(task_id, user_id)
            )
        """)
        await db.commit()

# --- Функции для работы с задачами ---
async def create_task(message_id: int, title: str, description: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (message_id, title, description) VALUES (?, ?, ?)",
            (message_id, title, description)
        )
        await db.commit()
        return cursor.lastrowid

async def get_task_by_message(message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Убрали type, которого нет в таблице
        async with db.execute(
            "SELECT id, thread_id, title, description, status, thread_message_id FROM tasks WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "thread_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "status": row[4],
                    "thread_message_id": row[5]
                }
    return None

async def get_task_by_id(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT message_id, thread_id, title, description, status, thread_message_id FROM tasks WHERE id = ?",
            (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "message_id": row[0],
                    "thread_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "status": row[4],
                    "thread_message_id": row[5]
                }
    return None

async def get_message_by_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT message_id FROM tasks WHERE id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_thread_message_id(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT thread_message_id FROM tasks WHERE id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_task_thread(task_id: int, thread_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET thread_id = ? WHERE id = ?", (thread_id, task_id))
        await db.commit()

async def set_thread_message(task_id: int, thread_message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET thread_message_id = ? WHERE id = ?", (thread_message_id, task_id))
        await db.commit()

async def get_task_members(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM task_members WHERE task_id = ?", (task_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def add_member(task_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO task_members (task_id, user_id) VALUES (?, ?)", (task_id, user_id))
        await db.commit()

async def remove_member(task_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM task_members WHERE task_id = ? AND user_id = ?", (task_id, user_id))
        await db.commit()

async def complete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
        await db.commit()