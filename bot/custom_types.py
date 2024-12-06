from pydantic import BaseModel

from aiogram.fsm.state import StatesGroup, State


class UserDTO(BaseModel):
    user_uid: int
    first_name: str
    last_name: str


class TimeWorkDTO(BaseModel):
    user_uid: int
    work_date: str
    work_start: str
    work_finish: str
    work_total: float


class TimeTracking(StatesGroup):
    start_time = State()
    end_time = State()


class RegisterStates(StatesGroup):
    first_and_last_name = State()
