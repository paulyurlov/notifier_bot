import logging
import os

import telebot
from get_series import (notify_series_next_week, notify_series_this_week,
                        notify_series_today, notify_series_tommorow)

TOKEN = os.getenv('BOT_TOKEN')
MY_ID = int(os.getenv('MY_ID'))
API_KEY = os.getenv('API_SECRET')


START_MESSAGE = "Прив =) ! Мои команды: \n\
\n/today - узнать какие сериалы выходят сегодня\
\n/tommorow - узнать какие сериалы выходят завтра\
\n/this_week - узнать какие сериалы выходят на этой неделе\
\n/next_week - узнать какие сериалы выходят на следующей неделе"


bot = telebot.TeleBot(TOKEN, parse_mode=None)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logging.info("Triggered /start or /help command")
    if message.from_user.id == MY_ID:
        bot.send_message(message.from_user.id, f"{START_MESSAGE}")


@bot.message_handler(commands=['today'])
def send_welcome(message):
    logging.info("Triggered /today command")
    if message.from_user.id == MY_ID:
        bot.send_message(message.from_user.id,
                         text=notify_series_today(API_KEY))


@bot.message_handler(commands=['tommorow'])
def send_welcome(message):
    logging.info("Triggered /tommorow command")
    if message.from_user.id == MY_ID:
        bot.send_message(message.from_user.id,
                         text=notify_series_tommorow(API_KEY))


@bot.message_handler(commands=['next_week'])
def send_welcome(message):
    if message.from_user.id == MY_ID:
        logging.info("Triggered /next_week command")
        bot.send_message(message.from_user.id,
                         text=notify_series_next_week(API_KEY))


@bot.message_handler(commands=['this_week'])
def send_welcome(message):
    if message.from_user.id == MY_ID:
        logging.info("Triggered /this_week command")
        bot.send_message(message.from_user.id,
                         text=notify_series_this_week(API_KEY))


logging.info("Bot starting polling")
bot.infinity_polling()
