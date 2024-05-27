import asyncio
import logging
import sys
from os import getenv
from aiogram import F, Router
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.methods.send_photo import SendPhoto
from aiogram.types import FSInputFile, reply_keyboard_markup, reply_keyboard_remove, keyboard_button, ContentType
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery

import yfinance as yf
import pytz
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib
from DatabaseIO import DatabaseIO
matplotlib.use("Agg")
app_token = "6611607409:AAGEPPaLyx9z-a07cqZl1l2exDAMXNaXDRs"

router = Router()

builder = ReplyKeyboardBuilder()
commands = ["/help", "/👛", "/📈"]


class CommandsStates(StatesGroup):
    graph_ticker_name = State()
    graph_ticker_start_date = State()
    graph_ticker_end_date = State()


loop = asyncio.get_event_loop()
db = DatabaseIO(user="postgres",
                password="1",
                database="postgres",
                host="127.0.0.1",
                loop=loop)

clear_states = InlineKeyboardBuilder().button(text="❌ Отменить", callback_data="clear_states")

for comm in commands:
    builder.button(text=comm)


@router.callback_query(F.data.startswith("clear_states"))
async def clear_state(query: CallbackQuery, state: FSMContext):
    s = await state.get_state()
    if s is not None:
        await query.bot.send_message(state.key.chat_id, f"Отменяю...")
        await state.clear()


@router.message(CommandsStates.graph_ticker_name)
async def message_handler(msg: Message, state: FSMContext):
    await msg.answer(f"Теперь введите начальную дату для сбора информации\nПример: 2020.1.1 - (1 января 2020 года)", reply_markup=clear_states.as_markup())
    await state.update_data(ticker_name=msg.text)
    await state.set_state(CommandsStates.graph_ticker_start_date)


@router.message(CommandsStates.graph_ticker_start_date)
async def message_handler(msg: Message, state: FSMContext):
    await msg.answer(f"Теперь введите конечную дату для сбора информации\nПример: 2020.1.1 - (1 января 2020 года)", reply_markup=clear_states.as_markup())
    await state.update_data(start_date=msg.text)
    await state.set_state(CommandsStates.graph_ticker_end_date)


@router.message(CommandsStates.graph_ticker_end_date)
async def message_handler(msg: Message, state: FSMContext):
    user_data = await state.get_data()
    await state.clear()

    await msg.answer(f"Скачиваю данные по тикеру {user_data['ticker_name']}")
    tz = pytz.timezone("America/New_York")
    start_date_split = user_data['start_date'].split(".")
    start = tz.localize(dt(int(start_date_split[0]), int(start_date_split[1]), int(start_date_split[2])))

    if msg.text.lower() == "сегодня":
        end = tz.localize(dt.today())
    else:
        end_date_split = msg.text.split(".")
        end = tz.localize(dt(int(end_date_split[0]), int(end_date_split[1]), int(end_date_split[2])))
    ticker_df = yf.download(start=start, end=end, tickers=user_data['ticker_name'], auto_adjust=True)
    if len(ticker_df) == 0:
       await msg.answer(f"Неизвестный тикер!")
       await msg.answer(f"Введите имя тикера", reply_markup=clear_states.as_markup())
       await state.set_state(CommandsStates.graph_ticker_name)
       return
    plt.plot(ticker_df['Close'])
    plt.title(f"История цен закрытия {user_data['ticker_name']}")
    name = f"{str(hash(msg.from_user.id))}.png"
    plt.savefig(name, dpi=300)
    plt.clf()
    await msg.answer_photo(photo=FSInputFile(name, user_data['ticker_name']))
    return


@router.message(CommandStart())
async def start_handler(msg: Message):
    result = await db.create_task(f"SELECT * FROM users WHERE user_id={msg.from_user.id}")
    if len(result) == 0:
        result = await db.create_task(f"INSERT INTO users VALUES ({msg.from_user.id})")
        await msg.answer(f"Привет, {html.bold(msg.from_user.full_name)}!", reply_markup=builder.as_markup())
    else:
        await msg.answer(f"Привет, {html.bold(msg.from_user.full_name)}, давно не виделись!", reply_markup=builder.as_markup())


@router.message(F.document)
async def msg_handler(msg: Message):
    file = await msg.bot.get_file(msg.document.file_id)
    result = await msg.bot.download_file(file.file_path, f"./downloaded_data/{msg.document.file_name}")


@router.message(StateFilter(None), Command(commands=["help"]))
async def help_handler(msg: Message):
    await msg.answer(f"аау")


@router.message(StateFilter(None), Command(commands=["👛"]))
async def set_token_handler(msg: Message, command: CommandObject):
    money_amount = await db.create_task(f"SELECT user_money_USDT FROM users WHERE user_id={msg.from_user.id}")
    await msg.answer(f"👛 Ваш баланс: {money_amount[0][0]} USDT!")


@router.message(StateFilter(None) and Command(commands=["📈"]))
async def graph_handler(msg: Message, state: FSMContext):
    await msg.answer(f"Введите имя тикера", reply_markup=clear_states.as_markup())
    await state.set_state(CommandsStates.graph_ticker_name)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(token=app_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await bot.delete_webhook(True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    loop.run_until_complete(main())