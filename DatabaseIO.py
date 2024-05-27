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
        self.conn = self.loop.run_until_complete(self.make_conn())

    async def make_conn(self):
        return await asyncpg.connect(user=self.user, password=self.password, database=self.database, host=self.host)

    async def tasks_handler(self, task):
        values = await self.conn.fetch(task)
        return values