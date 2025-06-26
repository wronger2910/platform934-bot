import logging
import random
import re
import os
import json
from aiogram import Bot, Dispatcher, executor, types
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"]), scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key("1TIGUiDIbCmHkqX3MUm4tqhNrKH1RQHkX-zD7ZvAWaE0").worksheet("Лист1")

# --- Telegram Bot Setup ---
API_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_ЗДЕСЬ")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}

prizes = [
    "🪄 Сувениры при посещении",
    "🧙‍♂️ 2 актёра в квест бесплатно",
    "🪄 Скидка на квест 30%",
    "🎁 Скидка на квест 50%",
    "🌀 Второй квест бесплатно",
    "🎉 Скидка на день рождения 5000₽",
    "📸 Фотограф в квесте на день рождения",
    "🏆 🟡 СУПЕР ПРИЗ: Бесплатный квест!"
]

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()
    user_data[user_id] = {
        'username': message.from_user.username,
        'source': args if args else 'не указан'
    }

    await message.answer(
        "🧙‍♂️ Добро пожаловать, юный магистр!\n\n"
        "Я — Волшебный Помощник центра квестов и праздников «Платформа 9¾». "
        "Позвольте записать Вас в наш волшебный список гостей... ✨\n\n"
        "📜 Как Вас зовут, о достойный маг?"
    )

@dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get('name') is None)
async def get_name(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text.strip()
    await message.answer(
        "🗓 Прекрасно! А когда Вы планируете визит к нам в Хогсмид? 🏰\n"
        "Пожалуйста, введите дату в формате **ДД.ММ.ГГГГ**, например: 04.08.2025"
    )

@dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get('visit_date') is None)
async def get_date(message: types.Message):
    user_id = message.from_user.id
    date_input = message.text.strip()
    if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_input):
        await message.answer("🕰 Ой-ой, мои песочные часы не понимают такой формат...\n"
                             "Введите дату как **ДД.ММ.ГГГГ**, например: 04.08.2025")
        return
    user_data[user_id]['visit_date'] = date_input
    await message.answer(
        "📞 Последний штрих — оставьте, пожалуйста, Ваш волшебный номер для связи, "
        "в формате **+7XXXXXXXXXX**"
    )

@dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get('phone') is None)
async def get_phone(message: types.Message):
    user_id = message.from_user.id
    phone_input = message.text.strip()
    if not re.match(r"^\+7\d{10}$", phone_input):
        await message.answer("🧙‍♂️ Ваш магический канал связи должен быть в формате **+7XXXXXXXXXX**.\nПопробуйте ещё раз:")
        return
    user_data[user_id]['phone'] = phone_input
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎁 Получить подарок")
    await message.answer("✨ Все магические сведения получены! Нажмите кнопку ниже, чтобы получить волшебный подарок 🎁", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🎁 Получить подарок")
async def give_prize(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    if 'prize' in user_data[user_id]:
        return

    prize = random.choice(prizes)
    user_data[user_id]['prize'] = prize

    remove_kb = types.ReplyKeyboardRemove()
    link_kb = types.InlineKeyboardMarkup()
    link_kb.add(types.InlineKeyboardButton("🎟 Забронировать посещение", url="https://platform934.ru/"))

    await message.answer(
        f"🎉 Поздравляем, Вы получили:\n\n{prize}\n\n"
        "📌 Подарком можно воспользоваться в течение **12 месяцев**. "
        "Просто покажите этот скрин менеджеру или администратору на площадке. ✨",
        reply_markup=remove_kb
    )

    await message.answer("🪄 Готовы к бронированию путешествия на Платформу 9¾?\nНажмите кнопку ниже ⬇️", reply_markup=link_kb)

    save_to_google_sheet(user_id)

def save_to_google_sheet(user_id):
    try:
        data = user_data[user_id]
        sheet.append_row([
            data.get('name', ''),
            data.get('visit_date', ''),
            data.get('phone', ''),
            data.get('prize', ''),
            str(user_id),
            data.get('username', ''),
            data.get('source', 'не указан')
        ])
        print(f"[✅ Данные добавлены в таблицу] {data.get('name')} | Источник: {data.get('source')}")
    except Exception as e:
        print(f"[⚠️ Ошибка при записи в таблицу] {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
