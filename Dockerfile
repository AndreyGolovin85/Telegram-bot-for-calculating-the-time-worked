FROM python:3.11-slim

RUN groupadd --gid 2000 node && useradd --uid 2000 --gid node --shell /bin/bash --create-home node
RUN apt update && apt install -y locales && locale-gen ru_RU.UTF-8

USER node

WORKDIR /appbot

ENV VIRTUAL_ENV=/appbot/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot/bot.py"]
