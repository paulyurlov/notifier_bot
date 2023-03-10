from manage_subscriptions import notify_subs
import os
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep
import logging


API_KEY = os.environ['API_SECRET']
BOT_TOKEN = os.environ['BOT_TOKEN']
MY_ID = os.environ['MY_ID']


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


class Notifier:
    def __init__(self, api_key: str, my_id: str, bot_token: str) -> None:
        self.__api_key = api_key
        self.__my_id = my_id
        self.__bot_token = bot_token
        self._scheduler = BackgroundScheduler()
        self._bot = telebot.TeleBot(self.__bot_token, parse_mode=None)

    def _mon_subs(self) -> None:
        self._bot.send_message(self.__my_id, text=notify_subs(self.__api_key))

    def start_mon(self, hour: int = 9, minute: str = "00") -> None:
        logging.info(f"Added cron job everyday on {hour}:{minute}")
        self._subs_job = self._scheduler.add_job(
            self._mon_subs, 'cron', hour=hour, minute=minute)
        self._scheduler.start()
        logging.info("Starting monitoring")
        while True:
            sleep(1)


nt = Notifier(API_KEY, MY_ID, BOT_TOKEN)
logging.info("Notifier is up")
nt.start_mon()
