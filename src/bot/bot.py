from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import asyncio

from src.api.core.config import Settings

settings = Settings()

API_TOKEN = settings.bot_token

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот, который может открыть ссылку для тебя.")

@dp.message(Command('open_link'))
async def open_link(message: types.Message):
    button = InlineKeyboardButton(text="Открыть ссылку", url="https://quantex-nine.vercel.app/")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    await message.reply("Нажми на кнопку ниже, чтобы открыть ссылку:", reply_markup=keyboard)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
