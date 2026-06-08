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
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import threading
import urllib.request
import time

def keep_alive():
    while True:
        try:
            urllib.request.urlopen("https://coachshax.onrender.com")
        except:
            pass
        time.sleep(600)

threading.Thread(target=keep_alive, daemon=True).start()

SCOPES=["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
import json as _json
creds=Credentials.from_service_account_info(_json.loads(os.environ["GOOGLE_CREDENTIALS"]),scopes=SCOPES)
gs=gspread.authorize(creds)
sheet=gs.open_by_key("10GU7L3gD840tNQemw8jrxegn454PqxwYIfvjm_ZAByg").sheet1

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='📅 Записаться на тренировку')],
    [KeyboardButton(text='👤 О тренере')],
    [KeyboardButton(text='💰 Мои тренировки')],
    [KeyboardButton(text='📦 Купить пакет')],
    [KeyboardButton(text='📱 Мои соцсети')],
], resize_keyboard=True)

class BookingForm(StatesGroup):
    name = State()
    phone = State()
    who = State()
    day = State()
    time = State()
    training_type = State()

class CheckForm(StatesGroup):
    phone = State()

@dp.my_chat_member()
async def on_user_join(event, bot: Bot):
    if event.new_chat_member.status == "member":
        await bot.send_message(event.chat.id, 'Привет! 👋 Я официальный бот тренера Coach Shax — Егора Шахметова.\n\nВот что я умею:\n\n📅 Записаться на тренировку — выбери тип, день и время\n💰 Мои тренировки — проверь сколько занятий осталось\n📦 Купить пакет — посмотри все варианты и цены\n👤 О тренере — узнай больше о Coach Shax\n📱 Соцсети — Instagram, TikTok, Telegram\n\nВыбери действие 👇', reply_markup=main_menu)

@dp.message(Command('start'))
async def start(message: Message):
    await message.answer('Привет! 👋 Я официальный бот тренера Coach Shax — Егора Шахметова.\n\nВот что я умею:\n\n📅 Записаться на тренировку — выбери тип, день и время\n💰 Мои тренировки — проверь сколько занятий осталось\n📦 Купить пакет — посмотри все варианты и цены\n👤 О тренере — узнай больше о Coach Shax\n📱 Соцсети — Instagram, TikTok, Telegram\n\nВыбери действие 👇', reply_markup=main_menu)

@dp.message(F.text == '👤 О тренере')
async def about(message: Message):
    await message.answer("Меня зовут Егор Шахметов, A.K.A Coach Shax — и я посвятил баскетболу 30 лет. Не слабо, правда?\n\nСвой путь начинал в спортивной школе Тринта, продолжил обучением и серьёзной карьерой в Америке — полная стипендия, двукратный All-American, Honorable Mention, финалист национального чемпионата NJCAA и много ещё чего. Потом 5 лет профессионального баскетбола в России.\n\nНо жизнь продолжается. Уже 9 лет я передаю этот опыт другим. Я знаю как достичь результата — какой бы ни была цель.\n\nРаботаю с детьми, подростками, взрослыми и профессионалами. Мне не важен твой уровень — важно куда ты хочешь прийти.\n\nГотов? Жми 👇\n📅 Записаться на тренировку")
    
@dp.message(F.text == '📦 Купить пакет')
async def packages(message: Message):
    await message.answer('🏀 ИНДИВИДУАЛЬНЫЕ ТРЕНИРОВКИ\n\n1 тренировка — 4 000 ₽\n4 тренировки — 13 000 ₽ (экономия 3 000 ₽)\n6 тренировок — 19 000 ₽ (экономия 5 000 ₽)\n8 тренировок — 25 000 ₽ (экономия 7 000 ₽)\n\n👥 SPLIT-ТРЕНИРОВКИ (2 человека)\n\n1 тренировка — 3 000 ₽ с человека / 90 мин\n4 тренировки — 9 500 ₽ с человека (экономия 2 500 ₽)\n6 тренировок — 13 000 ₽ с человека (экономия 5 000 ₽)\n\n👥 ГРУППОВЫЕ ТРЕНИРОВКИ (3+ человека)\n\n1 тренировка — 2 500 ₽ с человека / 90 мин\n4 тренировки — 8 000 ₽ с человека (экономия 2 000 ₽)\n6 тренировок — 11 000 ₽ с человека (экономия 4 000 ₽)\n\nДля записи нажмите: 📅 Записаться на тренировку')


@dp.message(F.text == '📱 Мои соцсети')
async def socials(message: Message):
    await message.answer("📱 Мои соцсети:\n\nInstagram: https://www.instagram.com/coach_shax\nTikTok: https://www.tiktok.com/@coach_shax\nTelegram: https://t.me/CoachShax")
@dp.message(F.text == '💰 Мои тренировки')
async def my_sessions(message: Message, state: FSMContext):
    await state.set_state(CheckForm.phone)
    await message.answer("Введите ваш номер телефона:")

@dp.message(CheckForm.phone)
async def check_sessions(message: Message, state: FSMContext):
    phone = message.text; rows = sheet.get_all_values(); await state.clear()
    found = False
    for row in rows:
        if len(row) > 1 and phone in row[1]:
            left = int(row[4])-int(row[5]) if len(row)>5 and row[4] and row[5] else row[4] if len(row)>4 and row[4] else "?"
            await message.answer("Ваше имя: " + row[0] + "\nОсталось тренировок: " + str(left)); found = True; break
    if not found: await message.answer("Номер не найден. Обратитесь к тренеру.")
    if not found: await message.answer("Номер не найден. Обратитесь к тренеру.")
@dp.message(F.text == '📅 Записаться на тренировку')
async def booking_start(message: Message, state: FSMContext):
    await state.set_state(BookingForm.training_type)
    type_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🏀 Индивидуальная')],
        [KeyboardButton(text='👥 Split (2 человека)')],
        [KeyboardButton(text='👥 Групповая (3+)')]
    ], resize_keyboard=True)
    await message.answer('Выберите тип тренировки:', reply_markup=type_kb)
    
@dp.message(BookingForm.training_type)
async def booking_training_type(message: Message, state: FSMContext):
    await state.update_data(training_type=message.text)
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
    training_type = data.get("training_type", "Индивидуальная")
    summary = f'Заявка принята.\nТип: {training_type}\nИмя: {data["name"]}\nТелефон: {data["phone"]}\nДень: {data["day"]}\nВремя: {data["time"]}'
    sheet.append_row([data["name"], data["phone"], data["day"], data["time"], "", "", "", training_type])
    await bot.send_message(482803603, "Новая заявка " + training_type + " " + data["name"] + " " + data["phone"] + " " + data["day"] + " " + data["time"])
    await message.answer(summary, reply_markup=main_menu)
    
@dp.message(Command("add"))
async def add_package(message: Message):
    if message.from_user.id != 482803603: return
    args = message.text.split()[1:]; name = " ".join(args[:-1]); count = int(args[-1])
    rows = sheet.get_all_values(); found = False
    for i, row in enumerate(rows):
        if name.lower() in row[0].lower(): sheet.update_cell(i+1, 5, count); found = True; break
    await message.answer("✅ Пакет добавлен: " + name + " — " + str(count) + " тренировок" if found else "❌ Клиент не найден")
@dp.message(Command("done"))
async def done_session(message: Message):
    if message.from_user.id != 482803603: return
    name = " ".join(message.text.split()[1:])
    rows = sheet.get_all_values(); found = False
    for i, row in enumerate(rows):
        if name.lower() in row[0].lower(): current = int(row[5]) if row[5] else 0; sheet.update_cell(i+1, 6, current+1); found = True; left = int(row[4]) - (current+1) if row[4] else 0; await message.answer("Тренировка засчитана. Осталось: " + str(left)); await bot.send_message(482803603, "ВНИМАНИЕ: У " + row[0] + " осталась 1 тренировка! Предложи купить пакет.") if left == 1 else None; break
    if not found: await message.answer("❌ Клиент не найден")
@dp.message(Command("clients"))
async def clients_list(message: Message):
    rows = sheet.get_all_values()[1:]; text = "Клиенты:\n\n"
    for row in rows:
        if row[0]: left = int(row[4])-int(row[5]) if row[4] and row[5] else row[4] if row[4] else "?"; text += row[0] + " - ostalось: " + str(left) + "\n"
    await message.answer(text if len(text) > 15 else "Клиентов пока нет")
async def send_reminders():
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            rows = sheet.get_all_values()[1:]
            for row in rows:
                if len(row) > 2 and row[2]:
                    try:
                        training_date = datetime.strptime(row[2].split()[0], "%d.%m")
                        training_date = training_date.replace(year=now.year)
                        if (training_date - now).days == 1:
                            time_str = row[3] if len(row) > 3 else ""
                            name = row[0]
                            await bot.send_message(482803603, f"⏰ НАПОМИНАНИЕ: Завтра тренировка!\n\nКлиент: {name}\nВремя: {time_str}")
                    except:
                        pass
        await asyncio.sleep(60)
async def main():
    session = AiohttpSession()
    print('Бот запущен')
    await bot.set_webhook("https://coachshax.onrender.com/webhook")
    app=web.Application()
    SimpleRequestHandler(dispatcher=dp,bot=bot).register(app,path="/webhook")
    setup_application(app,dp,bot=bot)
    runner=web.AppRunner(app)
    await runner.setup()
    site=web.TCPSite(runner,host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
    await site.start()
    asyncio.create_task(send_reminders())
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
