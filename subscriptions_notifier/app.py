from manage_subscriptions import notify_subs
from manage_series import notify_series
import os
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep


API_KEY = os.environ['API_SECRET']
BOT_TOKEN = os.environ['BOT_TOKEN']
MY_ID = os.environ['MY_ID']


class Notifier:
    def __init__(self, api_key: str, my_id: str, bot_token: str) -> None:
        self.__api_key = api_key
        self.__my_id = my_id
        self.__bot_token = bot_token
        self._scheduler = BackgroundScheduler()
        self._bot = telebot.TeleBot(self.__bot_token, parse_mode=None)

    def _mon_subs(self) -> None:
        self._bot.send_message(self.__my_id, text=notify_subs(self.__api_key))

    def _mon_series(self) -> None:
        self._bot.send_message(
            self.__my_id, text=notify_series(self.__api_key))

    def start_mon(self, hour: int = 9, minute: str = "00") -> None:
        self._subs_job = self._scheduler.add_job(
            self._mon_subs, 'cron', hour=hour, minute=minute)
        self._scheduler.start()
        while True:
            sleep(1)


nt = Notifier(API_KEY, MY_ID, BOT_TOKEN)
nt.start_mon()
