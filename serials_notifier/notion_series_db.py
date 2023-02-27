import requests
from datetime import datetime, time


NUM_TO_DAY = {
    1: "в понедельник",
    2: "во вторник",
    3: "в среду",
    4: "в четверг",
    5: "в пятницу",
    6: "в субботу",
    7: "в воскресенье"
}


def to_datetime(date_: str) -> datetime:
    """
    Transforms string date to datetime
    Args:
        date_ (str): string date

    Returns:
        datetime: datetime from string
    """
    return datetime.combine(datetime.strptime(date_, "%Y-%m-%d").date(), time(0, 0, 0))


class SeriesNotion:
    def __init__(self, api_key: str, db_id: str) -> None:
        """
        Init class
        Args:
            api_key (str): Notion api key string
            db_id (str): Notion database id string
        """
        self.api_key = api_key
        self.db_id = db_id

    @staticmethod
    def extract_data(req_res: list) -> list:
        """
        Extracts data from request result
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
                    "_id": el["id"],
                    "name": tmp["Название"]["title"][0]["text"]["content"],
                    "status": tmp["Статус"]["select"]["name"],
                }
                try:
                    sup["season"] = tmp["Сезон"]["number"]
                except:
                    sup["season"] = None
                try:
                    sup["is_finished"] = tmp["Закончен сезон?"]["select"]["name"]
                except:
                    sup["is_finished"] = "Нет"
                try:
                    sup["date_release"] = to_datetime(
                        tmp["Дата выхода"]["date"]["start"])
                except:
                    sup["date_release"] = None

                try:
                    sup["next_serie_date"] = to_datetime(
                        tmp["Следующая серия выйдет"]["date"]["start"])
                except:
                    sup["next_serie_date"] = None

                try:
                    sup["type"] = tmp["Тип"]["select"]["name"]
                except:
                    sup["type"] = None
                ret.append(sup)
            except:
                continue
        return ret

    def get_series(self) -> list:
        """_summary_

        Sends post request to notion api to get data from series database

        Returns:
            list: Returns list of series from series database
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        search_response = requests.post(
            f'https://api.notion.com/v1/databases/{self.db_id}/query', headers=headers)
        return self.extract_data(search_response.json())
