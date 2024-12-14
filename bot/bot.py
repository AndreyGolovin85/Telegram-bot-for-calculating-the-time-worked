import asyncio
import calendar
from datetime import datetime, timedelta
from typing import Literal
# import locale

from aiogram import Bot, types, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
import settings as setting
from custom_types import TimeTracking, RegisterStates
from utils import time_valid, count_work_time, register_user, create_work_time, list_work_days, get_production_calendar, \
    get_work_day, check_user_registration, calendar_selection

# locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
bot = Bot(token=setting.API_TOKEN)
ADMIN_ID = int(setting.ADMIN_ID)
dispatcher = Dispatcher()


def buttons_keyboard(data, keyboard_type: Literal["month_year", "choice_day"] = "month_year") \
        -> types.InlineKeyboardMarkup:
    """
    Формирует клавиатуру в зависимости от нужного варианта.
    """
    buttons_month_year = [
        types.InlineKeyboardButton(text=f"< {calendar.month_abbr[data.month - 1 if data.month > 1 else 12]}",
                                   callback_data=f"month_prev/{data.year}/{data.month}"),
        types.InlineKeyboardButton(text=f"{calendar.month_name[data.month]} {data.year}",
                                   callback_data=f"current/{data.year}/{data.month}"),
        types.InlineKeyboardButton(text=f"{calendar.month_abbr[data.month + 1 if data.month < 12 else 1]} >",
                                   callback_data=f"month_next/{data.year}/{data.month}"),
    ]
    if keyboard_type == "month_year":
        buttons = [buttons_month_year]
    elif keyboard_type == "choice_day":
        calendar_keyboard = create_calendar(data.year, data.month)
        buttons = calendar_keyboard
    else:
        buttons = []

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def create_calendar(year: int, month: int):
    """Функция для отрисовки кнопок календаря."""
    cal = calendar.monthcalendar(year, month)
    keyboard_rows = []
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(text="", callback_data="empty"))
            else:
                date_str = f"{day:02}-{month:02}-{year}"
                row.append(types.InlineKeyboardButton(text=str(day), callback_data=f"date/{date_str}"))
        keyboard_rows.append(row)

    navigation_row = [
        types.InlineKeyboardButton(text=f"< {calendar.month_abbr[month - 1 if month > 1 else 12]}",
                                   callback_data=f"month_prev_date/{year}/{month}"),
        types.InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}",
                                   callback_data=f" "),
        types.InlineKeyboardButton(text=f"{calendar.month_abbr[month + 1 if month < 12 else 1]} >",
                                   callback_data=f"month_next_date/{year}/{month}"),
    ]
    keyboard_rows.insert(0, navigation_row)

    return keyboard_rows


@dispatcher.callback_query(lambda call: call.data.startswith("month_"))
async def process_calendar_selection(callback: types.CallbackQuery):
    await callback.answer()
    try:
        current_date = datetime.now()
        data = callback.data.split("/")
        year, month = map(int, data[1:])
        if data[0] in ["month_prev", "month_next"]:
            date = calendar_selection(month, year, data[0])
            current_date = current_date.replace(year=date["year"], month=date["month"])
            buttons_keyboard(current_date)
            await callback.message.edit_text(text="Выберите месяц для просмотра отработанных дней:",
                                             reply_markup=buttons_keyboard(current_date))
            return
        if data[0] in ["month_prev_date", "month_next_date"]:
            date = calendar_selection(month, year, data[0])
            current_date = current_date.replace(year=date["year"], month=date["month"])
            buttons_keyboard(current_date)
            await callback.message.edit_text(text="Выберите день для записи отработанных часов:",
                                             reply_markup=buttons_keyboard(current_date, "choice_day"))
    except (IndexError, ValueError):
        await callback.message.answer("Ошибка обработки данных.")


@dispatcher.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Основные команды для работы:\n"
        "/register - Команда для регистрации.\n"
        "/write_work_time - Команда для записи отработанного времени.\n"
        "/show_work_time - Команда для просмотра отработанного времени.\n",
        parse_mode=ParseMode.HTML
    )


@dispatcher.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    if command.args == setting.ACCESS_KEY:
        is_admin = message.chat.id == ADMIN_ID
        await set_commands(is_admin)
        await message.answer(
            "Привет! Я бот для записи и подсчета отработанных часов.\n\n"
            "Для продолжения пройдите регистрацию /register.\n"
            "Или воспользуйтесь помощью по командам /help."
        )


@dispatcher.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext) -> None:
    if check_user_registration(message.chat.id):
        await message.answer("Вы уже зарегистрированы.")
        return

    await message.reply("Введите ваши имя и фамилию.\nНапример: Иван Иванов.\n"
                        "Или используйте /next, для использования данных из телеграмм профиля.")
    await state.update_data(chat_id=message.chat.id)
    await state.set_state(RegisterStates.first_and_last_name)


@dispatcher.message(RegisterStates.first_and_last_name)
async def process_name_and_department(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text == "/next":
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        if first_name and last_name:
            await register_user(user_uid=data.get('chat_id'), first_name=first_name, last_name=last_name)
            await message.reply(
                "Вы успешно зарегистрировались.\n"
                f"Имя: {first_name}\n"
                f"Фамилия: {last_name}\n"
                f"Для записи рабочего времени воспользуйтесь командой - /write_work_time"
            )
            await state.set_state(None)
            return
        await state.set_state(RegisterStates.first_and_last_name)
        await message.reply("Введите ваши имя и фамилию.\nНапример: Иван Иванов\n"
                            "Или используйте /next, для использования данных из телеграмм профиля.")
    first_and_last_name = message.text
    parts = first_and_last_name.split(" ")
    if len(parts) < 2:
        await message.reply("Неверный формат. Введите имя и фамилию.")
        await state.set_state(RegisterStates.first_and_last_name)
        return
    first_name = parts[0]
    last_name = parts[1]
    await register_user(user_uid=data.get('chat_id'), first_name=first_name, last_name=last_name)
    await message.reply(
        "Вы успешно зарегистрировались.\n"
        f"Имя: {first_name}\n"
        f"Фамилия: {last_name}\n\n"
        f"Для записи рабочего времени воспользуйтесь командой - /write_work_time"
    )
    await state.set_state(None)
    return


@dispatcher.message(Command("write_work_time"))
async def cmd_start_work(message: types.Message, state: FSMContext) -> None:
    if not check_user_registration(message.chat.id):
        await message.answer("Вы не зарегистрированы.\n"
                             "Для продолжения пройдите регистрацию /register.\n")
        return
    chat_id = message.chat.id
    current_date = datetime.now()
    work_date = current_date.strftime("%d-%m-%Y")
    work_day_in_db = get_work_day(chat_id, work_date)
    await state.update_data(work_day_in_db=work_day_in_db)
    if work_day_in_db is not None:
        await message.reply(f"Запись на {work_date} уже создана.")
        await message.answer(text="Выберите день для записи отработанных часов:",
                             reply_markup=buttons_keyboard(current_date, "choice_day"))
        return
    await message.reply("Отправьте время начала работы в формате ЧЧ:ММ.")
    await state.set_state(TimeTracking.start_time)


@dispatcher.callback_query(lambda call: call.data.startswith("date"))
async def date_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = callback.data.split("/")
    await callback.message.answer(text=f"{data[1]}")
    chat_id = callback.message.chat.id
    work_day_in_db = get_work_day(chat_id, data[1])
    await state.update_data(work_day_in_db=work_day_in_db)
    await state.update_data(date_time=data[1])
    await callback.message.edit_text("Отправьте время начала работы в формате ЧЧ:ММ.")
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
    if data.get("work_day_in_db") is not None:
        await message.reply(f"Запись отработанного времени на {data.get('date_time')} была создана ранее.")
        await state.set_state(None)
        return
    start_time = data.get("start_time")
    work_time = count_work_time(data.get("start_time"), data.get("end_time"))
    current_date = datetime.now()
    if data.get("date_time") is not None:
        work_date = data.get("date_time")
    else:
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
    if not check_user_registration(message.chat.id):
        await message.answer("Вы не зарегистрированы.\n"
                             "Для продолжения пройдите регистрацию /register.\n")
        return
    current_date = datetime.now()
    await message.answer(text="Выберите месяц для просмотра отработанных дней:",
                         reply_markup=buttons_keyboard(current_date))
    return


@dispatcher.callback_query(lambda call: call.data.startswith("current/"))
async def show_work_day(callback: types.CallbackQuery) -> None:
    user_id = callback.message.chat.id
    await callback.answer()
    data = callback.data.split("/")
    if data[0] == "current":
        year, month = map(int, callback.data.split("/")[1:])
        work_date = f"-{month:02}-{year}"
        production_calendar = get_production_calendar(month=f"{month:02}", year=f"{year}")
        sum_total = 0
        if not (user_work_days := list_work_days(user_uid=user_id, work_month_year=work_date)):
            await callback.message.edit_text(f"Вы не создали ни одной записи отработанных часов на "
                                             f"{calendar.month_name[month]}.\n"
                                             f"Норма часов в месяце: {production_calendar['working_hours']}.\n"
                                             f"Рабочих дней в месяце: {production_calendar['work_days']}.",
                                             reply_markup=None)
            return
        total_day = len(user_work_days)
        for user_work_day in user_work_days:
            sum_total += user_work_day.work_total
            await callback.message.answer(
                f"{user_work_day.work_date} - {user_work_day.work_total} с {user_work_day.work_start} до "
                f"{user_work_day.work_finish}")
        await callback.message.edit_text(f"Всего часов отработано: {sum_total},\n"
                                         f"Всего дней отработано: {total_day},\n"
                                         f"Норма часов в месяце: {production_calendar['working_hours']},\n"
                                         f"Рабочих дней в месяце: {production_calendar['work_days']}")
        return


async def set_commands(is_admin):
    if is_admin:
        commands = [
            BotCommand(command="register", description="Команда для регистрации"),
            BotCommand(command="write_work_time", description="Команда для записи отработанного времени"),
            BotCommand(command="show_work_time", description="Команда для просмотра отработанного времени"),
        ]
        await bot.set_my_commands(commands, BotCommandScopeChat(chat_id=ADMIN_ID))

    else:
        commands = [
            BotCommand(command="register", description="Команда для регистрации"),
            BotCommand(command="write_work_time", description="Команда для записи отработанного времени"),
            BotCommand(command="show_work_time", description="Команда для просмотра отработанного времени"),
        ]
        await bot.set_my_commands(commands, BotCommandScopeDefault())


async def generate_start_link(our_bot: Bot):
    return await create_start_link(our_bot, setting.ACCESS_KEY)


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
