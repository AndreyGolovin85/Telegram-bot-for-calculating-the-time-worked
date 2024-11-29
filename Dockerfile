FROM python:3.11-slim

RUN groupadd --gid 2000 node_bot && useradd --uid 2000 --gid node_bot --shell /bin/bash --create-home node_bot

USER node_bot

WORKDIR /app

ENV VIRTUAL_ENV=/app/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot/bot.py"]
