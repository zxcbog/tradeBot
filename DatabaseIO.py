import asyncpg
import threading
import asyncio
import asyncpg
import queue


class DatabaseIO:
    def __init__(self, user, password, database, host, loop):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.loop = loop

    async def create_task(self, task):
        task = self.loop.create_task(self.tasks_handler(task))
        return await task

    async def tasks_handler(self, task):
        conn = await asyncpg.connect(user=self.user, password=self.password,
                                     database=self.database, host=self.host)
        values = await conn.fetch(task)
        return values