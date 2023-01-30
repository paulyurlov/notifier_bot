import requests
import os
from datetime import datetime, timedelta, date


DB_ID = os.environ['SERIES_ID']


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


def get_series(api_key: str) -> list:
    headers = {
        "Authorization": f"Bearer {api_key}",
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }
    search_response = requests.post(
        f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=headers)
    return extract_data(search_response.json())


def update_serie_date(api_key: str, id: str, new_date: date):  # , data_to_upd: dict
    headers = {
        "Authorization": f"Bearer {api_key}",
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
        f'https://api.notion.com/v1/pages/{id}', headers=headers, json=data_to_upd)


def find_next(date_started):
    tmp = datetime.strptime(date_started, "%Y-%m-%d").date()
    while (tmp < datetime.today().date()):
        tmp += timedelta(days=7)
    return tmp.strftime('%Y-%m-%d')


def check_next_date(api_key: str):
    data = get_series(api_key)
    for el in data:
        if el["next_serie_date"] is None and el["if_finished"] == "Нет":
            update_serie_date(api_key, el["id"], find_next(el["release_date"]))
        elif el["if_finished"] == "Нет" and datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() < datetime.today().date():
            update_serie_date(api_key, el["id"], find_next(el["release_date"]))
        else:
            continue


def notify_series(api_key):
    check_next_date(api_key)
    text = f"#Сериалы \n\nСегодня выходят следующие сериалы:\n\n"
    space = "  "
    if_any = False
    for el in get_series(api_key):
        if el["if_finished"] == "Нет" and datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() == datetime.today().date():
            text += f"{space}{el['name']} \n"
            if_any = True
        elif el["if_finished"] == "Нет" and datetime.strptime(el["release_date"], "%Y-%m-%d").date() == datetime.today().date():
            text += f"{space}{el['name']} \n"
            if_any = True
    if if_any:
        return text
    return None
