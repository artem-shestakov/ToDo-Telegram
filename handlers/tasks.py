import aiohttp, os
from aiogram import F, Router, Bot, types
from aiogram.filters.text import Text
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from enum import Enum
from utils import post, get
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BACKEND = os.environ['BACKEND']
API_TOKEN = os.environ['API_TOKEN']

class TaskState(StatesGroup):
    tasks = State()
    task_new_title = State()
    task_new_description = State()

class TaskAction(str, Enum):
    done = "done"
    change_task = "change_task"

class TaskCallbackData(CallbackData, prefix="task"):
    action: TaskAction
    list_id: int
    task_id: int

router = Router()

@router.message(F.text == 'Yes', TaskState.tasks)
async def create_task_title(message: types.Message, state: FSMContext):
    await state.set_state(TaskState.task_new_title)
    await message.answer(
        "What is title of new task?",
        reply_markup=ReplyKeyboardRemove())

@router.message(F.text, TaskState.task_new_title)
async def create_list_description(message: types.Message, state: FSMContext):
    await state.update_data(task_title=message.text)
    await state.set_state(TaskState.task_new_description)
    await message.answer(
        "Description?",
        reply_markup=ReplyKeyboardRemove())

@router.message(F.text, TaskState.task_new_description)
async def save_task(message: types.Message, state: FSMContext):
    await state.update_data(list_description=message.text)
    user_data = await state.get_data()
    print(user_data)
    
    async with aiohttp.ClientSession() as session:
        resp = await post(
            session, 
            f"http://{BACKEND}/api/v1/lists/{user_data['current_list']}/tasks",
            headers={
                "X-Auth": API_TOKEN,
                "X-User": str(message.from_user.id)
            },
            json={
                "title": user_data['task_title'],
                "description": message.text,
            }
    )
    if resp['code'] == 201:
        kb_ok = InlineKeyboardBuilder()
        kb_ok.row(types.InlineKeyboardButton(text="Ok", callback_data=f"list:get_tasks:{user_data['current_list']}"))
        await state.set_state(TaskState.tasks)
        await message.answer(
            "Task was created",
            reply_markup=kb_ok.as_markup()
            )
    else:
        await state.set_state(TaskState.tasks)
        await message.answer("Произошла ошибка, попробуйте позже")