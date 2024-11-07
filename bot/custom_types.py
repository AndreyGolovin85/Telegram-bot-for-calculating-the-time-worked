from pydantic import BaseModel

from aiogram.fsm.state import StatesGroup, State


class UserDTO(BaseModel):
    user_uid: int
    first_name: str
    last_name: str


class TimeTracking(StatesGroup):
    start_time = State()
    end_time = State()
