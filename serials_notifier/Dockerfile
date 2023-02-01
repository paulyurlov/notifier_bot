# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster


RUN pip3 install pyTelegramBotAPI APScheduler

COPY . .

CMD [ "python3", "app.py"]