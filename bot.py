import asyncio
import gspread
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

SCOPES=["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
import json as _json
creds=Credentials.from_service_account_info(_json.loads(os.getenv("GOOGLE_CREDENTIALS","{}")),scopes=SCOPES)
gs=gspread.authorize(creds)
sheet=gs.open_by_key("10GU7L3gD840tNQemw8jrxegn454PqxwYIfvjm_ZAByg").sheet1

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
dp = Dispatcher(storage=MemoryStorage())

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='📅 Записаться на тренировку')],
    [KeyboardButton(text='👤 О тренере')],
    [KeyboardButton(text='💰 Мои тренировки')],
    [KeyboardButton(text='📦 Купить пакет')],
], resize_keyboard=True)

class BookingForm(StatesGroup):
    name = State()
    phone = State()
    who = State()
    day = State()
    time = State()

@dp.message(Command('start'))
async def start(message: Message):
    await message.answer('Привет. Я бот Coach Shax. Выбери действие:', reply_markup=main_menu)

@dp.message(F.text == '👤 О тренере')
async def about(message: Message):
    await message.answer('Егор Шахметов — профессиональный тренер по баскетболу. 30 лет в баскетболе, 10 лет тренерской карьеры. Учился и тренировался в США. Работаю с детьми, любителями и профессионалами.')

@dp.message(F.text == '📦 Купить пакет')
async def packages(message: Message):
    await message.answer('Пакеты тренировок:\n\n1 тренировка — 4 000 руб.\n4 тренировки — 13 000 руб. (экономия 3 000 руб.)\n8 тренировок — 25 000 руб. (экономия 7 000 руб.)\n\nДля записи нажмите: Записаться на тренировку')

@dp.message(F.text == '💰 Мои тренировки')
async def my_sessions(message: Message):
    await message.answer('Для просмотра ваших тренировок обратитесь к тренеру.')

@dp.message(F.text == '📅 Записаться на тренировку')
async def booking_start(message: Message, state: FSMContext):
    await state.set_state(BookingForm.name)
    await message.answer('Введите ваше ФИО:')

@dp.message(BookingForm.name)
async def booking_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingForm.phone)
    await message.answer('Введите ваш номер телефона:')

@dp.message(BookingForm.phone)
async def booking_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(BookingForm.who)
    who_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Для себя')],[KeyboardButton(text='Для ребенка')]], resize_keyboard=True)
    await message.answer('Для кого тренировка?', reply_markup=who_kb)

@dp.message(BookingForm.who)
async def booking_who(message: Message, state: FSMContext):
    await state.update_data(who=message.text)
    from datetime import datetime,timedelta
    today=datetime.now()
    days=[]
    for i in range(14):
        d=today+timedelta(days=i+1)
        if d.weekday() in [1,3,5,6]:
            days.append(d.strftime("%d.%m %A").replace("Tuesday","Вт").replace("Thursday","Чт").replace("Saturday","Сб").replace("Sunday","Вс"))
        if len(days)>=4:break
    day_kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=d)] for d in days],resize_keyboard=True)
    await state.set_state(BookingForm.day)
    await message.answer('Выберите день:', reply_markup=day_kb)

@dp.message(BookingForm.day)
async def booking_day(message: Message, state: FSMContext):
    if not any(c.isdigit() for c in message.text):
        await message.answer("Выберите день из кнопок")
        return
    await state.update_data(day=message.text)
    await state.set_state(BookingForm.time)
    time_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='10:00')],[KeyboardButton(text='12:00')],[KeyboardButton(text='14:00')],[KeyboardButton(text='16:00')]], resize_keyboard=True)
    await message.answer('Выберите время:', reply_markup=time_kb)

@dp.message(BookingForm.time)
async def booking_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    data = await state.get_data()
    await state.clear()
    summary = f'Заявка принята.\nИмя: {data["name"]}\nТелефон: {data["phone"]}\nДень: {data["day"]}\nВремя: {data["time"]}'
    sheet.append_row([data["name"], data["phone"], data["day"], data["time"]])
    await bot.send_message(482803603, "Новая заявка " + data["name"] + " " + data["phone"] + " " + data["day"] + " " + data["time"])
    await message.answer(summary, reply_markup=main_menu)

async def main():
    session = AiohttpSession()
    bot = Bot(token=BOT_TOKEN, session=session)
    print('Бот запущен')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
