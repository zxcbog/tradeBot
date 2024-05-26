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
from aiogram.types import FSInputFile

import yfinance as yf
import pytz
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
app_token = "6611607409:AAGEPPaLyx9z-a07cqZl1l2exDAMXNaXDRs"

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(msg: Message):
    await msg.answer(f"Привет, {html.bold(msg.from_user.full_name)}!")


@dp.message(Command(commands=["help"]))
async def help_handler(msg: Message):
    await msg.answer(f"аау")


@dp.message(Command(commands=["graph"]))
async def help_handler(msg: Message, command: CommandObject):
    args = command.args.split(" ")
    if args is not None and len(args) > 1:
        tz = pytz.timezone("America/New_York")
        start_date_split = args[1].split(".")
        start = tz.localize(dt(int(start_date_split[0]), int(start_date_split[1]), int(start_date_split[2])))
        if len(args) == 3:
            end_date_split = args[2].split(".")
            end = tz.localize(dt(int(end_date_split[0]), int(end_date_split[1]), int(end_date_split[2])))
        else:
            end = tz.localize(dt.today())
        ticker_df = yf.download(start=start, end=end, tickers=args[0], auto_adjust=True)
        plt.plot(ticker_df['Close'])
        name = f"{str(hash(msg.from_user.id))}.png"
        plt.savefig(name, dpi=300)
        plt.clf()
        await msg.answer_photo(photo=FSInputFile(name, args[0]))
    else:
        await msg.answer(f"Неверные аргументы команды. Пример: /graph 'ticker_name' '1.1.1999' '1.1.1999'")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=app_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # And the run events dispatching
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())