import logging
import calendar
from datetime import datetime
import requests
from aiogram.utils.formatting import as_list, Text

from models import User, Session, TimeWork
from custom_types import UserDTO, TimeWorkDTO

import settings as setting


def answer_reply(month: int, year: int, user_work_days: list | None, sum_total=0) -> Text:
    production_calendar = get_production_calendar(month=f"{month:02}", year=f"{year}")
    if user_work_days is None:
        return as_list(
            f"Вы не создали ни одной записи отработанных часов на "
            f"{calendar.month_name[month]}.\n"
            f"Норма часов в месяце: {production_calendar['working_hours']}.\n"
            f"Рабочих дней в месяце: {production_calendar['work_days']}."
        )
    total_day = len(user_work_days)
    return as_list(
        f"Всего часов отработано: {sum_total},\n"
        f"Всего дней отработано: {total_day},\n"
        f"Норма часов в месяце: {production_calendar['working_hours']},\n"
        f"Рабочих дней в месяце: {production_calendar['work_days']}"
    )


def get_production_calendar(month: str, year: str) -> dict:
    url = f"https://production-calendar.ru/get-period/{setting.PRODUCTION_CALENDAR}/ru/{month}.{year}/json?region=23"
    response = requests.get(url).json()["statistic"]
    return {"calendar_days": response["calendar_days"],
            "work_days": response["work_days"],
            "weekends": response["weekends"],
            "holidays": response["holidays"],
            "working_hours": response["working_hours"]}


def calendar_selection(month: int, year: int, data: str):
    month += 1 if data == "month_next" or data == "month_next_date" else -1
    if month > 12:
        year += 1
        month = 1
    elif month < 1:
        year -= 1
        month = 12
    return {"month": month, "year": year}


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
    """Создает запись отработанного дня в базу."""
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
    """Получает запись отработанного дня из базы данных по user_uid и дате."""
    with Session() as session:
        return session.query(TimeWork).filter_by(user_uid=user_uid, work_date=day).one_or_none()


def get_work_day_by_id(work_day_id: int) -> TimeWork | None:
    """Получает запись отработанного дня из базы данных по его id."""
    with Session() as session:
        work_day: TimeWork | None = session.query(TimeWork).filter_by(id=work_day_id).one_or_none()
        if not work_day:
            print(f"Тикет с id {work_day_id} не найден!")
            return
        return work_day


def delete_work_day_by_id(work_day_id: int) -> bool:
    """Удаляет запись из базы данных по ID."""
    with Session() as session:
        try:
            work_day = session.query(TimeWork).filter(TimeWork.id == work_day_id).one_or_none()
            if work_day:
                session.delete(work_day)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Ошибка при удалении записи: {e}")
            return False


def edit_work_day_by_id(work_day_id: int) -> bool:
    """Обновляет запись об отработанном дне по ID."""
    with Session() as session:
        try:
            work_day = session.query(TimeWork).filter_by(id=work_day_id).one_or_none()
            if work_day:
                work_day.updated_at = datetime.now(),
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Ошибка при обновлении записи: {e}")
            return False
