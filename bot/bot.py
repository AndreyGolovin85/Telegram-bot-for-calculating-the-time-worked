import asyncio
import calendar
from datetime import datetime, timedelta

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


async def create_calendar(year: int, month: int):
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
                row.append(types.InlineKeyboardButton(text=str(day), callback_data=date_str))
        keyboard_rows.append(row)

    # Навигация.  Создаем строки отдельно.
    navigation_row = [
        types.InlineKeyboardButton(text=f"< {calendar.month_abbr[month - 1 if month > 1 else 12]}",
                                   callback_data=f"prev_month/{year}/{month}"),
        types.InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}",
                                   callback_data=f"current/{year}/{month}"),
        types.InlineKeyboardButton(text=f"{calendar.month_abbr[month + 1 if month < 12 else 1]} >",
                                   callback_data=f"next_month/{year}/{month}"),
    ]
    keyboard_rows.insert(0, navigation_row)  # Вставляем строку навигации в начало

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    return keyboard


@dispatcher.callback_query(lambda call: call.data.startswith("current"))
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


@dispatcher.callback_query(lambda call: call.data)
async def process_calendar_selection(call: types.CallbackQuery):
    await call.answer()
    try:
        data = call.data.split("/")
        if data[0] in ["prev_month", "next_month"]:
            year, month = map(int, data[1:])
            month += 1 if data[0] == "next_month" else -1
            if month > 12:
                year += 1
                month = 1
            elif month < 1:
                year -= 1
                month = 12
            await call.message.edit_text("Выберите дату:", reply_markup=await create_calendar(year, month))
            return
    except (IndexError, ValueError):
        await call.message.answer("Ошибка обработки данных.")


async def generate_start_link(our_bot: Bot):
    return await create_start_link(our_bot, setting.ACCESS_KEY)


@dispatcher.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Основные команды для работы:\n"
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
        await register_user(user_uid=chat_id, first_name=first_name, last_name=last_name)
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
    keyboard = await create_calendar(current_date.year, current_date.month)
    await message.answer("Выберите месяц для просмотра отработанных дней:", reply_markup=keyboard)
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
