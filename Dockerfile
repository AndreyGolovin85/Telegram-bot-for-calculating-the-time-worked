FROM python:3.11-slim

RUN groupadd --gid 2000 nodetg && useradd --uid 2000 --gid nodetg --shell /bin/bash --create-home nodetg

USER nodetg

WORKDIR /appbot

ENV VIRTUAL_ENV=/appbot/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot/bot.py"]
