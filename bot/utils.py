from datetime import datetime

from models import User, Session

from custom_types import UserDTO


def time_valid(input_time: str) -> bool:
    try:
        hours = int(input_time.split(":")[0])
        minutes = int(input_time.split(":")[1])
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return True
    except ValueError:
        return False
    return False


def count_work_time(start_time: str, end_time: str) -> dict:
    if start_time and end_time:
        # Вычисляем отработанное время
        start_hours, start_minutes = map(int, start_time.split(':'))
        end_hours, end_minutes = map(int, end_time.split(':'))
        total_minutes = (end_hours * 60 + end_minutes) - (start_hours * 60 + start_minutes)
        total_hours = total_minutes // 60
        total_minutes %= 60
        if total_hours <= 4:
            total_hours = total_hours
        else:
            total_hours -= 1
        return {"total_hours": total_hours, "total_minutes": total_minutes}


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
