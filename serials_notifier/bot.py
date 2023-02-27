import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from mongo_series import SeriesMongo
from updater_worker import Updater


import asyncio
import aioschedule


API_KEY = os.environ['API_SECRET']
BOT_TOKEN = os.environ['BOT_TOKEN']
MY_ID = os.environ['MY_ID']
DB_ID = os.environ['SERIES_ID']
CON_STRING = os.environ['CON_STRING']


START_MESSAGE = "Прив =) ! Мои команды: \n\
\n/today - узнать какие сериалы выходят сегодня\
\n/tommorow - узнать какие сериалы выходят завтра\
\n/this_week - узнать какие сериалы выходят на этой неделе\
\n/next_week - узнать какие сериалы выходят на следующей неделе\
\n/wanted - вывести список сериалов, которые хочу посмотерть\
\n/update - обновить базы данных"


# Init bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# Init series MongoDB
series_db = SeriesMongo(CON_STRING)


# Init updater
updater = Updater(API_KEY, DB_ID, CON_STRING)


# Init logger
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    logging.info("Triggered /start or /help command")
    if message.from_user.id == int(MY_ID):
        await bot.send_message(message.from_user.id, f"{START_MESSAGE}")


@dp.message_handler(commands=['today'])
async def send_today(message: types.Message):
    logging.info("Triggered /today command")
    if message.from_user.id == int(MY_ID):
        await bot.send_message(message.from_user.id,
                               text=series_db.get_today())


@dp.message_handler(commands=['tommorow'])
async def send_tommorow(message: types.Message):
    logging.info("Triggered /tommorow command")
    if message.from_user.id == int(MY_ID):
        await bot.send_message(message.from_user.id,
                               text=series_db.get_tommorow())


@dp.message_handler(commands=['next_week'])
async def send_next_week(message: types.Message):
    if message.from_user.id == int(MY_ID):
        logging.info("Triggered /next_week command")
        await bot.send_message(message.from_user.id,
                               text=series_db.get_next_week())


@dp.message_handler(commands=['this_week'])
async def send_this_week(message: types.Message):
    if message.from_user.id == int(MY_ID):
        logging.info("Triggered /this_week command")
        await bot.send_message(message.from_user.id,
                               text=series_db.get_this_week())


@dp.message_handler(commands=['wanted'])
async def send_wanted_list(message: types.Message):
    if message.from_user.id == int(MY_ID):
        logging.info("Triggered /wanted command")
        await bot.send_message(message.from_user.id,
                               text=series_db.get_wanted())


@dp.message_handler(commands=['update'])
async def send_wanted_list(message: types.Message):
    if message.from_user.id == int(MY_ID):
        logging.info("Triggered /update command")
        await bot.send_message(message.from_user.id,
                               text='Запущен процесс обновления баз данных')
        updater.update_and_sync()


async def notify_sched() -> None:
    """
    Notification job
    """
    logging.info("Triggered scheduled notification command")
    await bot.send_message(int(MY_ID), text=series_db.get_today())


async def update_dbs() -> None:
    """
    Update and Sync DB job
    """
    logging.info("Triggered scheduled update command")
    updater.update_and_sync()


async def scheduler() -> None:
    """
    Create scheduler
    """
    aioschedule.every().day.at("11:30").do(notify_sched)
    aioschedule.every().day.at("20:30").do(notify_sched)
    aioschedule.every().day.at("00:00").do(update_dbs)
    aioschedule.every().day.at("03:00").do(update_dbs)
    aioschedule.every().day.at("07:00").do(update_dbs)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_) -> None:
    """
    Run scheduler on startup
    """
    asyncio.create_task(scheduler())


logging.info("Bot starting polling")
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
