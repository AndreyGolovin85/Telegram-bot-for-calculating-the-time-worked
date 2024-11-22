import asyncio
from datetime import datetime
import locale

from aiogram import Bot, types, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
import settings as setting
from custom_types import TimeTracking
from utils import time_valid, count_work_time, register_user, create_work_time, list_work_days, get_production_calendar, \
    get_work_day

bot = Bot(token=setting.API_TOKEN)
ADMIN_ID = int(setting.ADMIN_ID)
dispatcher = Dispatcher()
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")


async def generate_start_link(our_bot: Bot):
    return await create_start_link(our_bot, setting.ACCESS_KEY)


@dispatcher.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Основные команды для работы:\n"
        "/start_work - команда для регистрации пользователя.\n"
        "/write_work_time - Команда для записи отработанного времени.\n"
        "/show_work_time - Команда для просмотра отработанного времени.\n",
        parse_mode=ParseMode.HTML
    )


@dispatcher.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    if command.args == setting.ACCESS_KEY:
        chat_id = message.chat.id
        is_admin = message.chat.id == ADMIN_ID
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        user = await register_user(user_uid=chat_id, first_name=first_name, last_name=last_name)
        await set_commands(is_admin)
        await message.answer(
            "Привет! Я бот для записи и подсчета отработанных часов.\n\n"
            "Чтобы начать запись, отправьте команду /write_work_time.\n"
            "Или воспользуйтесь помощью по командам /help."
        )


@dispatcher.message(Command("write_work_time"))
async def cmd_start_work(message: types.Message, state: FSMContext) -> None:
    chat_id = message.chat.id
    current_date = datetime.now()
    work_date = current_date.strftime("%d-%m-%Y")
    work_day = get_work_day(chat_id, work_date)
    if work_day is not None:
        await message.reply("Запись на сегодня уже создана.")
        return
    await message.reply("Отправьте время начала работы в формате ЧЧ:ММ.")
    await state.set_state(TimeTracking.start_time)


@dispatcher.message(TimeTracking.start_time)
async def process_start_time(message: types.Message, state: FSMContext) -> None:
    start_time = message.text
    if time_valid(start_time) is False:
        await message.reply("Неверный формат. Введите время в формате ЧЧ:ММ.")
        return
    await state.update_data(start_time=start_time)
    await message.reply("Отправьте время окончания работы в формате ЧЧ:ММ.")
    await state.set_state(TimeTracking.end_time)


@dispatcher.message(TimeTracking.end_time)
async def process_end_time(message: types.Message, state: FSMContext) -> None:
    chat_id = message.chat.id
    end_time = message.text
    if time_valid(end_time) is False:
        await message.reply("Неверный формат. Введите время в формате ЧЧ:ММ.")
        return
    await state.update_data(end_time=end_time)
    data = await state.get_data()
    start_time = data.get("start_time")
    work_time = count_work_time(data.get("start_time"), data.get("end_time"))
    current_date = datetime.now()
    work_date = current_date.strftime("%d-%m-%Y")
    await create_work_time(chat_id, work_date, start_time, end_time, work_time)

    await message.reply(
        "Вы отработали:\n"
        f"Время начала работы: {data.get('start_time')}\n"
        f"Время окончания работы: {data.get('end_time')}\n"
        f"Дата: {work_date}\n"
        f"Отработано сегодня: {work_time} часов."
    )
    await state.set_state(None)
    return


@dispatcher.message(Command("show_work_time"))
async def cmd_work_time(message: types.Message, command: CommandObject) -> None:
    current_date = datetime.now()
    work_date = current_date.strftime("-%m-%Y")
    production_calendar = get_production_calendar(month=current_date.strftime("%m"), year=current_date.strftime("%Y"))
    user_work_days = list_work_days(user_uid=message.chat.id, work_month_year=work_date)
    sum_total = 0
    if message.chat.id != ADMIN_ID:
        if not (user_work_days := list_work_days(user_uid=message.chat.id)):
            await message.answer("Вы ещё не создали ни одной записи.")
            return
    total_day = len(user_work_days)
    for user_work_day in user_work_days:
        sum_total += user_work_day.work_total
        await message.answer(f"{user_work_day.work_date} - {user_work_day.work_total} с {user_work_day.work_start} до "
                             f"{user_work_day.work_finish}")
    await message.answer(f"Всего часов отработано : {sum_total},\n"
                         f"Всего дней отработано: {total_day},\n"
                         f"Норма часов в месяце: {production_calendar['working_hours']},\n"
                         f"Рабочих дней в месяце: {production_calendar['work_days']}")
    return


async def set_commands(is_admin):
    if is_admin:
        commands = [
            BotCommand(command="write_work_time", description="Команда для записи отработанного времени"),
            BotCommand(command="show_work_time", description="Команда для просмотра отработанного времени"),
        ]
        await bot.set_my_commands(commands, BotCommandScopeChat(chat_id=ADMIN_ID))

    else:
        commands = [
            BotCommand(command="write_work_time", description="Команда для записи отработанного времени"),
            BotCommand(command="show_work_time", description="Команда для просмотра отработанного времени"),
        ]
        await bot.set_my_commands(commands, BotCommandScopeDefault())


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
