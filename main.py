import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from utils import post, get
from handlers import lists, main_menu, tasks

BOT_TOKEN = os.environ['BOT_TOKEN']

logging.basicConfig(level=logging.INFO)

class ToDoStates(StatesGroup):
    start = State()
    registration = State()
    main_menu = State()
    list_new_name = State()
    list_new_description = State()
    list_new_save = State()
    lists = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_routers(main_menu.router, lists.router, tasks.router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
