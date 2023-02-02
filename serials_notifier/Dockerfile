# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster


RUN pip3 install aiogram aioschedule asyncio

COPY . .

CMD [ "python3", "bot.py"]