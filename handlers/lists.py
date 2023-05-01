import aiohttp, os
from aiogram import F, Router, Bot, types
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.filters.text import Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from enum import Enum
from utils import post, get
from .main_menu import kb_main_menu, MainMenuStates
from .tasks import TaskState, TaskCallbackData, TaskAction
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BACKEND = os.environ['BACKEND']
API_TOKEN = os.environ['API_TOKEN']

router = Router()

class ListAction(str, Enum):
    create_task = "create_task"
    get_tasks = "get_tasks"
    change_list = "change_list"

class ListCallbackData(CallbackData, prefix='list'):
    action: ListAction
    list_id: int


class ListStates(StatesGroup):
    list_new_name = State()
    list_new_description = State()
    list_new_save = State()
    lists = State()

# Get all lists
@router.message(F.text == 'My lists', MainMenuStates.main_menu)
@router.message(F.text == 'My lists', ListStates.lists)
@router.message(F.text == 'Return', TaskState.tasks)
async def get_all_lists(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        resp = await get(
            session, 
            f"http://{BACKEND}/api/v1/lists",
            headers={
                "X-Auth": API_TOKEN,
                "X-User": str(message.from_user.id)
            },
    )
    
    await state.set_state(ListStates.lists)
    await message.answer("Your lists", reply_markup=kb_main_menu.as_markup(resize_keyboard=True))
    if resp['code'] == 200:
        if resp['response']['lists']:
            for todo_list in resp['response']['lists']:
                text = f"{todo_list['title']}\n{todo_list['description']}"
                builder = InlineKeyboardBuilder()
                builder.row(
                    types.InlineKeyboardButton(text="Tasks", callback_data=ListCallbackData(action=ListAction.get_tasks, list_id=todo_list['id']).pack()),
                )
                await message.answer(text, reply_markup=builder.as_markup())
        else:
            await state.set_state(MainMenuStates.main_menu)
            await message.answer("You've not yet created list", reply_markup=kb_main_menu.as_markup(resize_keyboard=True))    
    else:
        await state.set_state(MainMenuStates.main_menu)
        await message.answer("Что-то пошло не так. Попробуйте еще раз.", reply_markup=kb_main_menu.as_markup(resize_keyboard=True))

# Get list's tasks
@router.callback_query(ListCallbackData.filter(F.action == ListAction.get_tasks), ListStates.lists)
@router.callback_query(ListCallbackData.filter(F.action == ListAction.get_tasks),TaskState.tasks)
async def get_list_tasks(callback: types.CallbackQuery, state: FSMContext, callback_data: ListCallbackData=None):
    print(callback_data.pack())
    async with aiohttp.ClientSession() as session:
        resp = await get(
            session, 
            f"http://{BACKEND}/api/v1/lists/{callback_data.list_id}/tasks",
            headers={
                "X-Auth": API_TOKEN,
                "X-User": str(callback.from_user.id)
            },
        )
    if resp['code'] == 200:
        await state.set_state(TaskState.tasks)
        if resp['response']['tasks']:
            for task in resp['response']['tasks']:
                text = f"{task['title']}\n{task['description']}"
                builder = InlineKeyboardBuilder()
                builder.row(
                    types.InlineKeyboardButton(text="Done", callback_data=TaskCallbackData(action=TaskAction.done, list_id=task['list_id'], task_id=task['id']).pack()),
                )
                await callback.message.answer(text, reply_markup=builder.as_markup())
        else:
            await callback.message.answer("No tasks")

        await state.update_data(current_list=callback_data.list_id)
        kb_create_task = ReplyKeyboardBuilder()
        kb_create_task.row(
            types.KeyboardButton(text="Yes"),
            types.KeyboardButton(text="Return")
        )
        await callback.message.answer("Create new task or return to lists?", reply_markup=kb_create_task.as_markup(resize_keyboard=True))
    else:
        callback.answer("Something goes wrong")    

@router.message(F.text == 'Create list', MainMenuStates.main_menu)
async def create_list_title(message: types.Message, state: FSMContext):
    await state.set_state(ListStates.list_new_name)
    await message.answer(
        "What is title of new list?",
        reply_markup=ReplyKeyboardRemove())
    
@router.message(F.text, ListStates.list_new_name)
async def create_list_description(message: types.Message, state: FSMContext):
    await state.update_data(list_title=message.text)
    await state.set_state(ListStates.list_new_description)
    await message.answer(
        "Description?",
        reply_markup=ReplyKeyboardRemove())

@router.message(F.text, ListStates.list_new_description)
async def save_list(message: types.Message, state: FSMContext):
    await state.update_data(list_description=message.text)
    user_data = await state.get_data()
    
    async with aiohttp.ClientSession() as session:
        resp = await post(
            session, 
            f"http://{BACKEND}/api/v1/lists",
            headers={
                "X-Auth": API_TOKEN,
                "X-User": str(message.from_user.id)
            },
            json={
                "title": user_data['list_title'],
                "description": message.text
            }
    )
    if resp['code'] == 201:
        await state.set_state(MainMenuStates.main_menu)
        await message.answer(
            "List was created",
            reply_markup=kb_main_menu.as_markup(resize_keyboard=True))
    else:
        await state.set_state(MainMenuStates.main_menu)
        await message.answer("Something goes wrong")