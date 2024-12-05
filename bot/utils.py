import logging
from datetime import datetime
import requests

from models import User, Session, TimeWork
from custom_types import UserDTO, TimeWorkDTO

import settings as setting


def get_production_calendar(month: str, year: str) -> dict:
    url = f"https://production-calendar.ru/get-period/{setting.PRODUCTION_CALENDAR}/ru/{month}.{year}/json?region=23"
    if month and year:
        logging.error(f"1111111111111111111 {month}, {year}, {url}")
    response = requests.get(url).json()["statistic"]
    return {"calendar_days": response["calendar_days"],
            "work_days": response["work_days"],
            "weekends": response["weekends"],
            "holidays": response["holidays"],
            "working_hours": response["working_hours"]}


def time_valid(input_time: str) -> bool:
    try:
        hours = int(input_time.split(":")[0])
        minutes = int(input_time.split(":")[1])
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return True
    except ValueError:
        return False
    return False


def count_work_time(start_time: str, end_time: str) -> float:
    if start_time and end_time:
        # Вычисляем отработанное время
        start_hours, start_minutes = map(int, start_time.split(':'))
        end_hours, end_minutes = map(int, end_time.split(':'))
        total_minutes = (end_hours * 60 + end_minutes) - (start_hours * 60 + start_minutes)
        if start_hours < end_hours:
            total_hours = total_minutes // 60
            total_minutes %= 60
        else:
            total_hours = 24 + (total_minutes // 60)
            total_minutes %= 60
        if total_hours <= 4:
            total_hours = total_hours
        else:
            total_hours -= 1
        return float(f"{total_hours}.{total_minutes}")


def check_user_registration(user_uid: int) -> User | None:
    return get_user_by_uid(user_uid)


def new_user(user_uid: int, first_name: str, last_name: str) -> UserDTO:
    return UserDTO(user_uid=user_uid, first_name=first_name, last_name=last_name)


async def register_user(user_uid: int, first_name: str, last_name: str):
    user = check_user_registration(user_uid)
    if not user:
        user_data = new_user(user_uid, first_name, last_name)
        add_user(user_data)


def get_user_by_uid(user_uid: int) -> User | None:
    with Session() as session:
        return session.query(User).filter_by(user_uid=user_uid).one_or_none()


def add_user(user_data: UserDTO) -> User:
    with Session() as session:
        user = User(
            user_uid=user_data.user_uid,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(user)
        session.commit()
        return user


def work_time_data(user_uid: int, work_date: str, work_start: str, work_finish: str, work_total: float) -> TimeWorkDTO:
    return TimeWorkDTO(user_uid=user_uid, work_date=work_date, work_start=work_start, work_finish=work_finish,
                       work_total=work_total)


async def create_work_time(user_uid: int, work_date: str, work_start: str, work_finish: str, work_total: float):
    time_data = work_time_data(user_uid, work_date, work_start, work_finish, work_total)
    add_work_time(time_data)


def add_work_time(time_data: TimeWorkDTO) -> int:
    with Session() as session:
        new_time = TimeWork(
            user_uid=time_data.user_uid,
            work_date=time_data.work_date,
            work_start=time_data.work_start,
            work_finish=time_data.work_finish,
            work_total=time_data.work_total,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(new_time)
        session.commit()
        return new_time.id


def list_work_days(user_uid, work_month_year: str | None = None) -> list:
    """Функция для выборки отработанных дней в месяце определенным пользователем."""
    with Session() as session:
        select_work_days = session.query(TimeWork).filter_by(user_uid=user_uid).order_by(TimeWork.work_date)\
            .filter(TimeWork.work_date.contains(work_month_year))
        work_days = [day for day in select_work_days]

        return work_days


def get_work_day(user_uid: int, day: str) -> TimeWork | None:
    with Session() as session:
        return session.query(TimeWork).filter_by(user_uid=user_uid, work_date=day).one_or_none()
