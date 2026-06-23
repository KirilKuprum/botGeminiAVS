import asyncio
import json
import random
import requests
from os import getenv
from dotenv import load_dotenv
from PromptBuilder import PromptBuilder

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from google import genai

from PromptBuilder import PromptBuilder
from db import DataBase

dp = Dispatcher()
client = None
bot = None
test_db = None

def auth_db():
    try:
        return DataBase(table_name="TestTable", region="us-east-1")
    except Exception as err:
        print(f"Помилка БД: {type(err)}: {err}")
        return None

def auth_telegram():
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN provided")
    return Bot(token=token)

def auth_gemini_api():
    api_key = getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY provided.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Помилка ініціалізації Gemini: {e}")
        return None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Let's talk, dude!")

@dp.message(Command("db"))
async def cmd_db(message: Message):
    if test_db:
        await message.answer(str(test_db))
    else:
        await message.answer("База даних не підключена.")

@dp.message(Command("db_add"))
async def cmd_db_add(message: Message):
    arg = message.text.removeprefix("/db_add ")
    try:
        test_db.put_item(json.loads(arg))
        await message.answer("Дані успішно додані до БД.")
    except Exception as err:
        await message.answer(f"Помилка БД: {err}")

@dp.message(Command("roll"))
async def cmd_roll(message: Message):
    await message.answer(f"Ви викинули {random.randint(1, 100)}")

@dp.message(Command("meowfact"))
async def cmd_meowfact(message: Message):
    args = message.text.split()[1:]
    count = int(args[0]) if args else 1
    response = requests.get("https://meowfacts.herokuapp.com/", {"count": count})
    if response.ok:
        facts = response.json()['data']
        await message.answer("\n\n".join(facts))
    else:
        await message.answer("Something wrong!")

@dp.message()
async def any_message(message: Message):
    if client is None:
        await message.answer("ШІ сервіс не налаштований.")
        return

    try:
        prompt = PromptBuilder.simplePrompt(message.text)
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-1.5-flash",
            contents=prompt
        )
        await message.answer(response.text)
    except Exception as err:
        print(f"Помилка ШІ: {err}")
        await message.answer("Щось пішло не так при спілкуванні з ШІ.")

async def main():
    global bot, client, test_db

    load_dotenv()
    bot = auth_telegram()
    client = auth_gemini_api()
    test_db = auth_db()

    print("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())