import logging
from datetime import datetime, time, timedelta

import pymongo
import requests

from notion_series_db import SeriesNotion

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


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


class Updater:

    def __init__(self, api_key: str, db_id: str, con_string: str) -> None:
        """
        Init class
        Args:
            api_key (str): Notion api key string
            db_id (str): Notion database id string
            con_string (str): MongoDB connection string
        """

        self.mongo_client = pymongo.MongoClient(con_string)
        self.db = self.mongo_client.series['series']

        self.api_key = api_key
        self.db_id = db_id

        self.notion_db = SeriesNotion(self.api_key, self.db_id)

    @staticmethod
    def find_next(date_started: datetime) -> datetime:
        """
        Computes new series date based on previous date
        Args:
            date_started (datetime): previous date

        Returns:
            _type_: new date
        """

        tmp = date_started.date()
        while (tmp < datetime.today().date()):
            tmp += timedelta(days=7)
        return datetime.combine(tmp, time(0, 0, 0))

    def insert_one(self, data: dict) -> None:
        """
        Inserts one serie into notion database
        Args:
            data (dict): Data to insert
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

        json_data = {
            "parent": {"database_id": self.db_id},
            "properties": dict()
        }

        for k, v in data.items():
            if v is not None:
                match k:
                    case 'name':
                        json_data["properties"]["Название"] = {
                            "title": [
                                {
                                    "text": {
                                        "content": v
                                    }
                                }
                            ]
                        }
                    case 'status':
                        json_data["properties"]['Статус'] = {
                            "select": {
                                "name": v,
                            }
                        }
                    case 'season':
                        json_data["properties"]['Сезон'] = {
                            "number": v
                        }
                    case 'date_release':
                        json_data["properties"]['Дата выхода'] = {
                            "date": {
                                "start": v.strftime('%Y-%m-%d'),
                                "end": None,
                                "time_zone": None
                            }
                        }
                    case 'next_serie_date':
                        json_data["properties"]['Следующая серия выйдет'] = {
                            "date": {
                                "start": v.strftime('%Y-%m-%d'),
                                "end": None,
                                "time_zone": None
                            }
                        }
                    case 'is_finished':
                        json_data["properties"]['Закончен сезон?'] = {
                            "select": {
                                "name": v,
                            }
                        }
                    case 'type':
                        json_data["properties"]['Тип'] = {
                            "select": {
                                "name": v,
                            }
                        }
        res = requests.post(
            f'https://api.notion.com/v1/pages', headers=headers, json=json_data)

        if str(res) == '<Response [200]>':
            logging.info(f"Succesfully inserted page and got response {res}")
        else:
            logging.warning(f"Something went wrong got response {res}")

    def update_serie_date(self, serie_id: str, old_date: datetime) -> None:
        """
        Updates next serie release date

        Args:
            serie_id (str): series id in notion db
            old_date (datetime): series old next serie date
        """
        new_date = old_date
        if old_date < datetime.today():
            new_date = self.find_next()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        data_to_upd = {
            "properties": {
                "Следующая серия выйдет": {
                    "date": {
                        "start": new_date.strftime('%Y-%m-%d'),
                        "end": None,
                        "time_zone": None
                    }
                }
            }
        }
        res = requests.patch(
            f'https://api.notion.com/v1/pages/{serie_id}', headers=headers, json=data_to_upd)

        if str(res) == '<Response [200]>':
            logging.info(f"Succesfully deleted page and got response {res}")
        else:
            logging.warning(f"Something went wrong got response {res}")

    def del_one(self, serie_id: str) -> None:
        """
        Updates serie based on id
        Args:
            data (dict): data to update
            serie_id (str): notion series page id
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        res = requests.delete(
            f'https://api.notion.com/v1/blocks/{serie_id}', headers=headers)

        if str(res) == '<Response [200]>':
            logging.info(f"Succesfully deleted page and got response {res}")
        else:
            logging.warning(f"Something went wrong got response {res}")

    def notion_to_mongo(self) -> None:
        """
        Insert new data from notion to mongo
        """
        self.db.drop()
        self.db = self.mongo_client.series['series']

        all_ser_notion = self.notion_db.get_series()

        for el in all_ser_notion:
            del el['_id']

        for el in all_ser_notion:
            self.db.insert_one(el)

    def update_dates(self) -> None:
        """
        Update next serie dates
        """

        logging.info("Started update_and_sync function \n\n")
        all_ser_notion = self.notion_db.get_series()

        for el in all_ser_notion:
            self.del_one(el['_id'])

        all_ser_mongo = list(self.db.find({}))

        for el in all_ser_mongo:
            self.update_serie_date(el['_id'], el["next_serie_date"])

        self.notion_to_mongo()
        logging.info("Finished updating and syncing \n\n")
