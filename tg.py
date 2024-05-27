import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.methods.send_photo import SendPhoto
from aiogram.types import FSInputFile, reply_keyboard_markup, reply_keyboard_remove, keyboard_button
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import yfinance as yf
import pytz
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib
from DatabaseIO import DatabaseIO
matplotlib.use("Agg")
app_token = "our_token"

dp = Dispatcher()

builder = ReplyKeyboardBuilder()
commands = ["/help", "/graph"]


loop = asyncio.get_event_loop()
db = DatabaseIO(user="postgres",
                password="1",
                database="postgres",
                host="127.0.0.1",
                loop=loop)

for comm in commands:
    builder.button(text=comm)


@dp.message(CommandStart())
async def start_handler(msg: Message):
    result = await db.create_task(f"SELECT * FROM users WHERE user_id={msg.from_user.id}")
    if len(result) == 0:
        result = await db.create_task(f"INSERT INTO users VALUES ({msg.from_user.id})")
        await msg.answer(f"Привет, {html.bold(msg.from_user.full_name)}!", reply_markup=builder.as_markup())
    else:
        await msg.answer(f"Привет, {html.bold(msg.from_user.full_name)}, давно не виделись!", reply_markup=builder.as_markup())


@dp.message(Command(commands=["help"]))
async def help_handler(msg: Message):
    await msg.answer(f"аау")


@dp.message(Command(commands=["set_token"]))
async def set_token_handler(msg: Message, command: CommandObject):
    args = command.args.split(" ")
    if len(args) == 2:
        result = await db.create_task(f"SELECT * FROM markets WHERE LOWER(market_name) LIKE '{args[0].lower()}'")
        if len(result) == 0:
            await msg.answer(f"Неизвестная биржа - {args[0]}")
            return
        market_id = result[0][0]
        result = await db.create_task(f"SELECT * FROM user_api_tokens WHERE user_id={msg.from_user.id} AND market_id={market_id}")
        if len(result) == 0:
            result = await db.create_task(f"INSERT INTO user_api_tokens(user_id,market_id,api_token) VALUES ({msg.from_user.id}, {market_id}, '{args[1]}')")
            await msg.answer(f"Данные успешно добавлены!")
        else:
            result = await db.create_task(f"UPDATE user_api_tokens "
                                          f"SET user_id = {msg.from_user.id}, market_id = {market_id}, api_token = '{args[1]}' "
                                          f"WHERE user_id={msg.from_user.id} AND market_id={market_id}")
            await msg.answer(f"Данные успешно обновлены!")



@dp.message(Command(commands=["graph"]))
async def graph_handler(msg: Message, command: CommandObject):
    if command.args is not None:
        args = command.args.split(" ")
        if len(args) > 1:
            await msg.answer(f"Скачиваю данные по тикеру {args[0]}")
            tz = pytz.timezone("America/New_York")
            start_date_split = args[1].split(".")
            start = tz.localize(dt(int(start_date_split[0]), int(start_date_split[1]), int(start_date_split[2])))
            if len(args) == 3:
                end_date_split = args[2].split(".")
                end = tz.localize(dt(int(end_date_split[0]), int(end_date_split[1]), int(end_date_split[2])))
            else:
                end = tz.localize(dt.today())
            ticker_df = yf.download(start=start, end=end, tickers=args[0], auto_adjust=True)
            if len(ticker_df) == 0:
                await msg.answer(f"Неизвестный тикер")
                return
            plt.plot(ticker_df['Close'])
            name = f"{str(hash(msg.from_user.id))}.png"
            plt.savefig(name, dpi=300)
            plt.clf()
            await msg.answer_photo(photo=FSInputFile(name, args[0]))
        else:
            await msg.answer(f"Неверные аргументы команды. Пример: /graph 'ticker_name' '1.1.1999' '1.1.1999'")
    else:
        await msg.answer(f"Неверные аргументы команды. Пример: /graph 'ticker_name' '1.1.1999' '1.1.1999'")

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
bot = Bot(token=app_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
loop.run_until_complete(dp.start_polling(bot))