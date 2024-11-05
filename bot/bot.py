import asyncio

from aiogram import Bot, types, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.deep_linking import create_start_link
import settings as setting
from utils import time_valid, count_work_time

bot = Bot(token=setting.API_TOKEN)
ADMIN_ID = int(setting.ADMIN_ID)
dispatcher = Dispatcher()


class TimeTracking(StatesGroup):
    start_time = State()
    end_time = State()


async def generate_start_link(our_bot: Bot):
    return await create_start_link(our_bot, setting.ACCESS_KEY)


@dispatcher.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Основные команды для работы:\n"
        "/start_work - команда для регистрации пользователя.\n",
        parse_mode=ParseMode.HTML,
    )


@dispatcher.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    if command.args == setting.ACCESS_KEY:
        await message.answer(
            "Привет! Я бот для записи и подсчета отработанных часов.\n\n"
            "Чтобы начать запись, отправьте команду /write_work_time.\n"
            "Или воспользуйтесь помощью по командам /help."
        )


@dispatcher.message(Command("write_work_time"))
async def cmd_start_work(message: types.Message, state: FSMContext) -> None:
    await message.reply("Отправьте время начала работы в формате ЧЧ:ММ.")
    await state.set_state(TimeTracking.start_time)


@dispatcher.message(TimeTracking.start_time)
async def process_name_and_department(message: types.Message, state: FSMContext) -> None:
    start_time = message.text
    if time_valid(start_time) is False:
        await message.reply("Неверный формат. Введите время в формате ЧЧ:ММ.")
        return
    await state.update_data(start_time=start_time)
    await message.reply("Отправьте время окончания работы в формате ЧЧ:ММ.")
    await state.set_state(TimeTracking.end_time)


@dispatcher.message(TimeTracking.end_time)
async def process_department(message: types.Message, state: FSMContext) -> None:
    end_time = message.text
    if time_valid(end_time) is False:
        await message.reply("Неверный формат. Введите время в формате ЧЧ:ММ.")
        return
    await state.update_data(end_time=end_time)
    data = await state.get_data()
    work_time = count_work_time(data.get('start_time'), data.get('end_time'))

    await message.reply(
        "Проверьте данные и подтвердите.\n"
        f"Время начала работы: {data.get('start_time')}\n"
        f"Время окончания работы: {data.get('end_time')}\n"
        f"Всего отработано: {work_time['total_hours']}.{work_time['total_minutes']}"
    )


async def main():
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Бот запущен, приглашение работает по ссылке {await generate_start_link(bot)}",
    )
    await dispatcher.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    setting.setup_logging(log_file="bot.log")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановка сервера!")
