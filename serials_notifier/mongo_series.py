import pymongo
from datetime import datetime, time, timedelta
from typing import Tuple


'''
 DB Structure
    {
        "_id": ObjectId("1234567890"),
        "name": "Истребитель демонов 2",
        "season": 2,
        "status": "Смотрю", ["Смотрю", "Хочу посмотреть", "Просмотренно"]
        "date_release": "2022-07-08" BSON date,
        "next_serie_date": "2022-07-15",
        "is_finished": "Да", ["Нет", "Да"]
        "type": "Аниме", ["Аниме", "Сериал", "Мультсериал"]
    }

'''


NUM_TO_DAY = {
    1: "в понедельник",
    2: "во вторник",
    3: "в среду",
    4: "в четверг",
    5: "в пятницу",
    6: "в субботу",
    7: "в воскресенье"
}


class SeriesMongo:
    def __init__(self, con_string: str) -> None:
        """
        Init DB
        Args:
            con_string (str): MongoDB connection string
        """

        self.mongo_client = pymongo.MongoClient(con_string)
        self.db = self.mongo_client.series['series']

    @staticmethod
    def today() -> datetime:
        """
        Get today but time is 00:00:00

        Returns:
            datetime: datetime today but time is 00:00:00
        """
        return datetime.combine(datetime.now().date(), time(0, 0, 0))

    @staticmethod
    def next_week() -> Tuple[datetime, datetime]:
        """
        Get next week interval [monday, sunday]

        Returns:
            Tuple[date, date]: Returns next week interval [monday, sunday]
        """
        today_ = datetime.combine(datetime.now().date(), time(0, 0, 0))
        monday = today_ - \
            timedelta(days=(today_.isoweekday() - 1)) + timedelta(days=7)
        sunday = monday + timedelta(days=6)
        return (monday, sunday)

    @staticmethod
    def this_week() -> Tuple[datetime, datetime]:
        """
        Get this week interval [monday, sunday]

        Returns:
            Tuple[date, date]: Returns this week interval [monday, sunday]
        """
        today_ = datetime.combine(datetime.now().date(), time(0, 0, 0))
        monday = today_ - timedelta(days=(today_.isoweekday() - 1))
        sunday = monday + timedelta(days=6)
        return (monday, sunday)

    def get_today(self) -> str:
        """

        Creates notification string for series that come out today

        Returns:
            str: notification string for series that come out today
        """

        text = f"#Сериалы \n\nСегодня выходят следующие сериалы:\n\n"
        space = "  "

        cursor = self.db.find(
            {'status': 'Смотрю', 'is_finished': {'$ne': 'Да'}, 'next_serie_date': {"$eq": self.today()}}).sort("next_serie_date", pymongo.ASCENDING)

        list_series = list(cursor)
        if len(list_series) == 0:
            return "Сегодня ничего не выходит =("

        for item in list_series:
            text += f"{space}{item['name']} \n"

        return text

    def get_tommorow(self) -> str:
        """
        Creates notification string for series that come out tommorow

        Returns:
            str: notification string for series that come out tommorow
        """

        """

        Creates notification string for series that come out today

        Returns:
            str: notification string for series that come out today
        """

        text = f"#Сериалы \n\nЗавтра выходят следующие сериалы:\n\n"
        space = "  "

        cursor = self.db.find(
            {'status': 'Смотрю', 'is_finished': {'$ne': 'Да'}, 'next_serie_date': {"$eq": self.today() + timedelta(days=1)}}).sort("next_serie_date", pymongo.ASCENDING)

        list_series = list(cursor)

        if len(list_series) == 0:
            return "Завтра ничего не выходит =("

        for item in list_series:
            text += f"{space}{item['name']} \n"

        return text

    def get_next_week(self) -> str:
        """
        Creates notification string for series that come out next week

        Returns:
            str: notification string for series that come out next week
        """

        text = f"#Сериалы \n\nНа следующей неделе выходят:\n\n"
        space = "  "

        mon, sun = self.next_week()
        cursor = self.db.find(
            {'status': 'Смотрю', 'is_finished': {'$ne': 'Да'}, 'next_serie_date': {"$gte": mon, "$lte": sun}}).sort("next_serie_date", pymongo.ASCENDING)

        list_series = list(cursor)

        if len(list_series) == 0:
            return "На следующей неделе ничего не выходит =("

        for item in list_series:
            text += f"{space}{item['name']} \n"

        return text

    def get_this_week(self) -> str:
        """
        Creates notification string for series that come out this week

        Returns:
            str: notification string for series that come out this week
        """

        intro = "#Сериалы \n\n"
        already_text = "Уже вышли:\n\n"
        text = f"На этой неделе выходят:\n\n"
        space = "  "
        if_already = False

        mon, sun = self.this_week()
        cursor = self.db.find({"$and": [
            {'status': 'Смотрю'},
            {'is_finished': {'$ne': 'Да'}},
            {"$or": [
                {'next_serie_date': {"$gte": mon, "$lte": sun}},
                {'next_serie_date': {
                    "$gte": mon + timedelta(days=7), "$lt": self.today() + timedelta(days=7)}}]}
        ]}).sort("next_serie_date", pymongo.ASCENDING)

        list_series = list(cursor)

        if len(list_series) == 0:
            return "На этой неделе ничего не выходит =("

        for item in list_series:
            if (item['next_serie_date'] < self.today()) or ((item['next_serie_date'] - timedelta(days=7) < self.today()) and item['next_serie_date'] - timedelta(days=7) > mon):
                already_text += f"{space}{item['name']} вышел {NUM_TO_DAY[item['next_serie_date'].isoweekday()]}\n"
                if_already = True
            elif item['next_serie_date'] == self.today():
                text += f"{space}{item['name']} выходит сегодня\n"
            elif item['next_serie_date'] > self.today() and item['next_serie_date'] <= sun:
                text += f"{space}{item['name']} выходит {NUM_TO_DAY[item['next_serie_date'].isoweekday()]}\n"
        if if_already:
            return intro + already_text + "\n\n" + text
        return intro + text

    def get_wanted(self) -> str:
        """
        Creates notification string for series that come out this week

        Returns:
            str: notification string for series that come out this week
        """

        intro = "#Сериалы \n\n"
        text = f"Вот ожидаемые сериалы:\n\n"
        space = "  "

        cursor = self.db.find({'status': 'Хочу посмотреть'})

        list_series = list(cursor)

        if len(list_series) == 0:
            return "Список ожидаемых пуст =("

        for item in list_series:
            if item['date_release'] is None:
                text += f"{space}{item['name']} дата выхода не известна или он уже вышел \n \n"

            elif item['date_release'] <= self.today():
                text += f"{space}{item['name']} уже выходит \n \n"

            elif item['date_release'] > self.today():
                text += f"{space}{item['name']} выходит {item['date_release'].date()} \n \n"
        return intro + text
