import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from manage_series import series_notion


import asyncio
import aioschedule


API_KEY = os.environ['API_SECRET']
BOT_TOKEN = os.environ['BOT_TOKEN']
MY_ID = os.environ['MY_ID']
DB_ID = os.environ['SERIES_ID']


START_MESSAGE = "Прив =) ! Мои команды: \n\
\n/today - узнать какие сериалы выходят сегодня\
\n/tommorow - узнать какие сериалы выходят завтра\
\n/this_week - узнать какие сериалы выходят на этой неделе\
\n/next_week - узнать какие сериалы выходят на следующей неделе"\


series_manager = series_notion(DB_ID, API_KEY)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    logging.info("Triggered /start or /help command")
    if message.from_user.id == MY_ID:
        await bot.send_message(message.from_user.id, f"{START_MESSAGE}")


@dp.message_handler(commands=['today'])
async def send_today(message: types.Message):
    logging.info("Triggered /today command")
    if message.from_user.id == MY_ID:
        await bot.send_message(message.from_user.id,
                               text=series_manager.notify_series_today())


@dp.message_handler(commands=['tommorow'])
async def send_tommorow(message: types.Message):
    logging.info("Triggered /tommorow command")
    if message.from_user.id == MY_ID:
        await bot.send_message(message.from_user.id,
                               text=series_manager.notify_series_tommorow())


@dp.message_handler(commands=['next_week'])
async def send_next_week(message: types.Message):
    if message.from_user.id == MY_ID:
        logging.info("Triggered /next_week command")
        await bot.send_message(message.from_user.id,
                               text=series_manager.notify_series_next_week())


@dp.message_handler(commands=['this_week'])
async def send_this_week(message: types.Message):
    if message.from_user.id == MY_ID:
        logging.info("Triggered /this_week command")
        await bot.send_message(message.from_user.id,
                               text=series_manager.notify_series_this_week())


async def notify_sched() -> None:
    logging.info("Triggered scheduled job command")
    await bot.send_message(MY_ID, text=series_manager.notify_series_today())


async def scheduler() -> None:
    aioschedule.every().day.at("11:15").do(notify_sched)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_) -> None:
    asyncio.create_task(scheduler())


logging.info("Bot starting polling")
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
