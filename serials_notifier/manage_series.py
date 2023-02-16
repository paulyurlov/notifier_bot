import requests
from datetime import datetime, timedelta, date
from typing import Tuple
import os


API_KEY = os.environ['API_SECRET']
DB_ID = os.environ['SERIES_ID']


NUM_TO_DAY = {
    1: "в понедельник",
    2: "во вторник",
    3: "в среду",
    4: "в четверг",
    5: "в пятницу",
    6: "в субботу",
    7: "в воскресенье"
}


class series_notion:
    def __init__(self) -> None:
        pass

    @staticmethod
    def find_next(date_started):
        tmp = datetime.strptime(date_started, "%Y-%m-%d").date()
        while (tmp < datetime.today().date()):
            tmp += timedelta(days=7)
        return tmp.strftime('%Y-%m-%d')

    @staticmethod
    def get_next_week() -> Tuple[date, date]:
        """_summary_

        Get next week interval [monday, sunday]

        Returns:
            Tuple[date, date]: Returns next week interval [monday, sunday]
        """
        today = datetime.today().date()
        monday = today - \
            timedelta(days=(today.isoweekday() - 1)) + timedelta(days=7)
        sunday = monday + timedelta(days=6)
        return (monday, sunday)

    @staticmethod
    def get_this_week() -> Tuple[date, date]:
        """_summary_

        Get this week interval [monday, sunday]

        Returns:
            Tuple[date, date]: Returns this week interval [monday, sunday]
        """
        today = datetime.today().date()
        monday = today - timedelta(days=(today.isoweekday() - 1))
        sunday = monday + timedelta(days=6)
        return (monday, sunday)

    @staticmethod
    def extract_data(req_res: list) -> list:
        """_summary_

        Args:
            req_res (list): Request result from notion api

        Returns:
            list: aggregated data from series database
        """
        ret = list()
        for el in req_res["results"]:
            try:
                tmp = el["properties"]
                sup = {
                    "id": el["id"],
                    "name": tmp["Название"]["title"][0]["text"]["content"],
                    "status": tmp["Статус"]["select"]["name"],
                    "season": tmp["Сезон"]["number"]
                }
                try:
                    sup["if_finished"] = tmp["Закончен сезон?"]["select"]["name"]
                except:
                    sup["if_finished"] = "Нет"
                try:
                    sup["release_date"] = tmp["Дата выхода"]["date"]["start"]
                except:
                    sup["release_date"] = None

                try:
                    sup["next_serie_date"] = tmp["Следующая серия выйдет"]["date"]["start"]
                except:
                    sup["next_serie_date"] = None
                ret.append(sup)
            except:

                continue
        return ret

    @classmethod
    def get_series(self) -> list:
        """_summary_

        Sends post request to notion api to get data from series database

        Returns:
            list: Returns list of series from series database
        """
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        search_response = requests.post(
            f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=headers)
        return self.extract_data(search_response.json())

    @classmethod
    def update_serie_date(self, serie_id: str, new_date: date) -> None:
        """_summary_

        Updates next serie release date

        Args:
            new_date (date): New release date to be set for serie by its id
        """
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        data_to_upd = {
            "properties": {
                "Следующая серия выйдет": {
                    "date": {
                        "start": new_date,
                        "end": None,
                        "time_zone": None
                    }
                }
            }
        }
        _ = requests.patch(
            f'https://api.notion.com/v1/pages/{serie_id}', headers=headers, json=data_to_upd)

    @classmethod
    def check_next_date(self) -> None:
        """_summary_

        Checks if next serie release date is up to date, and if not updates it

        """
        data = self.get_series()
        for el in data:
            if el["next_serie_date"] is None and el["status"] == 'Смотрю' and el["release_date"] is not None and el["if_finished"] == "Нет":
                self.update_serie_date(
                    el["id"], self.find_next(el["release_date"]))
            elif el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and el["release_date"] is not None and datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() < datetime.today().date():
                self.update_serie_date(
                    el["id"], self.find_next(el["release_date"]))
            else:
                continue

    @classmethod
    def get_sorted_series(self) -> list:
        """_summary_

        Returns sorted series by date

        """
        ret = list()
        data = self.get_series()
        for el in data:
            if el["next_serie_date"] is not None:
                ret.append(el)
            elif el["release_date"] is not None:
                ret.append(el)
            else:
                continue

        return sorted(ret, key=lambda el: datetime.strptime(el["next_serie_date"], "%Y-%m-%d").weekday() if el["next_serie_date"] is not None else datetime.strptime(el["release_date"], "%Y-%m-%d").weekday())

    @classmethod
    def notify_series_today(self) -> str:
        """_summary_

        Creates notification string for series that come out today

        Returns:
            str: notification string for series that come out today
        """
        self.check_next_date()
        text = f"#Сериалы \n\nСегодня выходят следующие сериалы:\n\n"
        space = "  "
        if_any = False
        for el in self.get_sorted_series():
            if el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() == datetime.today().date():
                text += f"{space}{el['name']} \n"
                if_any = True
            elif el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and datetime.strptime(el["release_date"], "%Y-%m-%d").date() == datetime.today().date():
                text += f"{space}{el['name']} \n"
                if_any = True
        if if_any:
            return text
        return "Сегодня ничего не выходит =("

    @classmethod
    def notify_series_tommorow(self) -> str:
        """_summary_

        Creates notification string for series that come out tommorow

        Returns:
            str: notification string for series that come out tommorow
        """
        self.check_next_date()
        text = f"#Сериалы \n\nЗавтра выходят следующие сериалы:\n\n"
        space = "  "
        if_any = False
        for el in self.get_sorted_series():
            if el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d") - timedelta(days=1)).date() == datetime.today().date():
                text += f"{space}{el['name']} \n"
                if_any = True
            elif el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and (datetime.strptime(el["release_date"], "%Y-%m-%d") - timedelta(days=1)).date() == datetime.today().date():
                text += f"{space}{el['name']} \n"
                if_any = True
        if if_any:
            return text
        return "Завтра ничего не выходит =("

    @classmethod
    def notify_series_next_week(self) -> str:
        """_summary_

        Creates notification string for series that come out next week

        Returns:
            str: notification string for series that come out next week
        """
        self.check_next_date()
        text = f"#Сериалы \n\nНа следующей неделе выходят:\n\n"
        space = "  "
        if_any = False
        mon, sun = self.get_next_week()
        for el in self.get_sorted_series():
            if el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() >= mon):
                tmp_day = datetime.strptime(
                    el["next_serie_date"], "%Y-%m-%d").isoweekday()
                text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
                if_any = True
            elif el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() + timedelta(days=7)) <= sun) and ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() + timedelta(days=7)) >= mon):
                tmp_day = datetime.strptime(
                    el["next_serie_date"], "%Y-%m-%d").isoweekday()
                text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
                if_any = True
            elif el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() >= mon):
                tmp_day = datetime.strptime(
                    el["release_date"], "%Y-%m-%d").isoweekday()
                text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
                if_any = True
        if if_any:
            return text
        return "На следующей неделе ничего не выходит =("

    @classmethod
    def notify_series_this_week(self) -> str:
        """_summary_

        Creates notification string for series that come out this week

        Returns:
            str: notification string for series that come out this week
        """
        self.check_next_date()
        intro = "#Сериалы \n\n"
        already_text = "Уже вышли:\n"
        text = f"На этой неделе выходят:\n\n"
        space = "  "
        if_any = False
        if_already = False
        mon, sun = self.get_this_week()
        for el in self.get_sorted_series():
            if el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and (((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() >= mon)) or ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() - timedelta(days=7)) < datetime.today().date() and ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() - timedelta(days=7)) <= sun) and ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() - timedelta(days=7)) >= mon))):
                if (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() - timedelta(days=7)) < datetime.today().date() and ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() - timedelta(days=7)) <= sun) and ((datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() - timedelta(days=7)) >= mon):
                    tmp_day = datetime.strptime(
                        el["next_serie_date"], "%Y-%m-%d").isoweekday()
                    already_text += f"{space}{el['name']} вышел {NUM_TO_DAY[tmp_day]}\n"
                    if_any = True
                    if_already = True
                elif datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() == datetime.today().date():
                    tmp_day = datetime.strptime(
                        el["next_serie_date"], "%Y-%m-%d").isoweekday()
                    text += f"{space}{el['name']} выходит сегодня\n"
                    if_any = True
                else:
                    tmp_day = datetime.strptime(
                        el["next_serie_date"], "%Y-%m-%d").isoweekday()
                    text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
                    if_any = True
            elif el["if_finished"] == "Нет" and el["status"] == 'Смотрю' and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() >= mon):
                if datetime.strptime(el["release_date"], "%Y-%m-%d").date() < datetime.today().date():
                    tmp_day = datetime.strptime(
                        el["release_date"], "%Y-%m-%d").isoweekday()
                    already_text += f"{space}{el['name']} вышел {NUM_TO_DAY[tmp_day]}\n"
                    if_any = True
                    if_already = True
                elif datetime.strptime(el["release_date"], "%Y-%m-%d").date() == datetime.today().date():
                    tmp_day = datetime.strptime(
                        el["release_date"], "%Y-%m-%d").isoweekday()
                    text += f"{space}{el['name']} выходит сегодня\n"
                    if_any = True
                else:
                    tmp_day = datetime.strptime(
                        el["release_date"], "%Y-%m-%d").isoweekday()
                    text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
                    if_any = True
        if if_any:
            if if_already:
                return intro + already_text + "\n\n" + text
            return intro + text
        return "На этой неделе ничего не выходит =("

    @classmethod
    def list_wanted(self) -> str:
        """_summary_

        Creates notification string for series that come out this week

        Returns:
            str: notification string for series that come out this week
        """
        self.check_next_date()
        intro = "#Сериалы \n\n"
        text = f"Вот ожидаемые сериалы:\n\n"
        space = "  "
        for el in self.get_series():
            ser = ''
            try:
                if el['status'] == 'Хочу посмотреть':
                    try:
                        ser = f"{el['name']} выходит {el['release_date']} \n"
                    except:
                        ser = f"{el['name']} дата выхода не известна или он уже вышел \n"
            except:
                continue
            text += space + ser
        return intro + text
