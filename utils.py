from aiogram import Router
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.state import State, StatesGroup
from DatabaseIO import DatabaseIO
import asyncio

from config import user, passwd, dbase, host

router = Router()

builder = ReplyKeyboardBuilder()
commands = ["/help", "/👛", "/📈"]


class CommandsStates(StatesGroup):
    graph_ticker_name = State()
    graph_ticker_start_date = State()
    graph_ticker_end_date = State()


loop = asyncio.get_event_loop()
db = DatabaseIO(user=user,
                password=passwd,
                database=dbase,
                host=host,
                loop=loop)

clear_states = InlineKeyboardBuilder().button(text="❌ Отменить", callback_data="clear_states")

for comm in commands:
    builder.button(text=comm)