import requests
import os
from datetime import datetime


DB_ID = os.environ['SUBS_ID']


def extract_data(req_res):
    ret = list()
    for el in req_res["results"]:
        tmp = el["properties"]
        sup = {
            "name": tmp["Подписка"]["title"][0]["text"]["content"],
            "type": tmp["Тип"]["select"]["name"],
            "prcie": tmp["Цена"]["number"],
            "total_pay": tmp["Я плочу"]["formula"]["number"],
            "duration": tmp["Период"]["select"]["name"],
            "month_pay": tmp["Я плочу в месяц"]["formula"]["number"]
        }
        try:
            sup["date_activated"] = tmp["Дата списания"]["date"]["start"]
        except:
            sup["date_activated"] = None
        ret.append(sup)
    return ret


def get_subs(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }
    search_response = requests.post(
        f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=headers)
    return extract_data(search_response.json())


def notify_subs(api_key):
    text = f"#Подписки \n\nСкоро нужно оплатить следующие подписки:\n\n"
    space = "  "
    for el in get_subs(api_key):
        if el["date_activated"] is not None:
            if (datetime.strptime(
                    el["date_activated"], "%Y-%m-%d").date() - datetime.today().date()).days <= 2:
                if el['duration'] == "Годовая":
                    if el['type'] == "Семейная подписка":
                        text += f"{space}{el['name']} к оплате {el['price']} руб. до {'-'.join(reversed(el['date_activated'].split('-')))}\n{space}Это семейная годовая подписка, нужно попросить денег с членов семьи"
                    else:
                        text += f"{space}{el['name']} к оплате {el['total_pay']} руб. до {'-'.join(reversed(el['date_activated'].split('-')))}\n{space}Это личная годовая подписка"
                else:
                    if el['type'] == "Семейная подписка":
                        text += f"{space}{el['name']} к оплате {el['price']} до {'-'.join(reversed(el['date_activated'].split('-')))}\n{space}Это семейная ежемесячная подписка, нужно попросить денег с членов семьи"
                    else:
                        text += f"{space}{el['name']} к оплате {el['total_pay']} руб. до {'-'.join(reversed(el['date_activated'].split('-')))}\n{space}Это личная ежемесячная подписка"
                text += "\n\n"
    return text
