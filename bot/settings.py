from dotenv import load_dotenv
import os
import sys
import logging


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
PRODUCTION_CALENDAR = os.getenv("PRODUCTION_CALENDAR")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")


engine = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
#engine = "sqlite:///bot.db"


def setup_logging(log_file, level=logging.INFO):
    """
    Настройка базового логгера.
    """

    logging.basicConfig(
        level=level,
        format="[%(asctime)s] - %(filename)s:%(lineno)d #%(levelname)-s - %(name)s - %(message)s",
        #filename=log_file,
        #filemode="w",
    )

    if not API_TOKEN or not ADMIN_ID or not ACCESS_KEY:
        logging.error("Отсутствуют переменные ENV.")
        sys.exit(1)
