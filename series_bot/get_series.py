import os
from datetime import date, datetime, timedelta

import requests


DB_ID = os.environ['SERIES_ID']


def get_next_week():
    today = datetime.today().date()
    monday = today - \
        timedelta(days=(today.isoweekday() - 1)) + timedelta(days=7)
    sunday = monday + timedelta(days=6)
    return (monday, sunday)


def get_this_week():
    today = datetime.today().date()
    monday = today - timedelta(days=(today.isoweekday() - 1))
    sunday = monday + timedelta(days=6)
    return (monday, sunday)


NUM_TO_DAY = {
    1: "в понедельник",
    2: "во вторник",
    3: "в среду",
    4: "в четверг",
    5: "в пятницу",
    6: "в субботу",
    7: "в воскресенье"
}


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


def update_serie_date(api_key: str, id: str, new_date: date) -> None:  # , data_to_upd: dict
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


def find_next(date_started: str) -> str:
    tmp = datetime.strptime(date_started, "%Y-%m-%d").date()
    while (tmp < datetime.today().date()):
        tmp += timedelta(days=7)
    return tmp.strftime('%Y-%m-%d')


def check_next_date(api_key: str) -> None:
    data = get_series(api_key)
    for el in data:
        if el["next_serie_date"] is None and el["if_finished"] == "Нет":
            update_serie_date(api_key, el["id"], find_next(el["release_date"]))
        elif el["if_finished"] == "Нет" and datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() < datetime.today().date():
            update_serie_date(api_key, el["id"], find_next(el["release_date"]))
        else:
            continue


def notify_series_today(api_key: str) -> str:
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
    return "Сегодня ничего не выходит =("


def notify_series_tommorow(api_key: str) -> str:
    check_next_date(api_key)
    text = f"#Сериалы \n\nЗавтра выходят следующие сериалы:\n\n"
    space = "  "
    if_any = False
    for el in get_series(api_key):
        if el["if_finished"] == "Нет" and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d") - timedelta(days=1)).date() == datetime.today().date():
            text += f"{space}{el['name']} \n"
            if_any = True
        elif el["if_finished"] == "Нет" and (datetime.strptime(el["release_date"], "%Y-%m-%d") - timedelta(days=1)).date() == datetime.today().date():
            text += f"{space}{el['name']} \n"
            if_any = True
    if if_any:
        return text
    return "Завтра ничего не выходит =("


def notify_series_next_week(api_key: str) -> str:
    check_next_date(api_key)
    text = f"#Сериалы \n\nНа следующей неделе выходят:\n\n"
    space = "  "
    if_any = False
    mon, sun = get_next_week()
    for el in get_series(api_key):
        if el["if_finished"] == "Нет" and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() >= mon):
            tmp_day = datetime.strptime(
                el["next_serie_date"], "%Y-%m-%d").isoweekday()
            text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
            if_any = True
        elif el["if_finished"] == "Нет" and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() >= mon):
            tmp_day = datetime.strptime(
                el["release_date"], "%Y-%m-%d").isoweekday()
            text += f"{space}{el['name']} выходит {NUM_TO_DAY[tmp_day]}\n"
            if_any = True
    if if_any:
        return text
    return "На следующей неделе ничего не выходит =("


def notify_series_this_week(api_key: str) -> str:
    check_next_date(api_key)
    intro = "#Сериалы \n\n"
    already_text = "Уже вышли:\n"
    text = f"На этой неделе выходят:\n\n"
    space = "  "
    if_any = False
    if_already = False
    mon, sun = get_this_week()
    for el in get_series(api_key):
        if el["if_finished"] == "Нет" and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() >= mon):
            if datetime.strptime(el["next_serie_date"], "%Y-%m-%d").date() < datetime.today().date():
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
        elif el["if_finished"] == "Нет" and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() <= sun) and (datetime.strptime(el["release_date"], "%Y-%m-%d").date() >= mon):
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
