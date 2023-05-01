import aiohttp, os
from aiogram import F, Router, Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from utils import post, get

BACKEND = os.environ['BACKEND']
API_TOKEN = os.environ['API_TOKEN']

router = Router()

class MainMenuStates(StatesGroup):
    start = State()
    registration = State()
    main_menu = State()

kb_main_menu = ReplyKeyboardBuilder()
kb_main_menu.row(
    types.KeyboardButton(text="My lists"),
    types.KeyboardButton(text="Create list")
)

@router.message(Command("start"))
async def cmd_start(message: types.Message, bot: Bot, state: FSMContext):
    print(message.from_user.id)
    async with aiohttp.ClientSession() as session:
        resp = await post(
            session, 
            f"http://{BACKEND}/auth/get-user",
            headers={
                "X-Auth": API_TOKEN
            },
            json={
                "user_id": message.from_user.id
            }
    )
    if resp['code'] != 200:
        builder = ReplyKeyboardBuilder()
        builder.row(types.KeyboardButton(text="Auth", request_contact=True))
        await state.set_state(MainMenuStates.registration)
        await message.answer("Необходимо зарегистрироваться", reply_markup=builder.as_markup(resize_keyboard=True))
    else:
        await state.set_state(MainMenuStates.main_menu)
        await message.answer(f"Добрый день, {message.from_user.username}!", reply_markup=kb_main_menu.as_markup(resize_keyboard=True))

@router.message(F.contact, MainMenuStates.registration)
async def btn(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        resp = await post(
            session, 
            f"http://{BACKEND}/auth/sign-up",
            headers={
                "X-Auth": API_TOKEN
            },
            json={
                "user_id": message.contact.user_id,
                "first_name": message.contact.first_name,
                "last_name": message.contact.last_name
            }
    )
    if resp['code'] != 201:
        await message.answer("Произошла ошибка, попробуйте позже")
    else:
        await state.set_state(MainMenuStates.main_menu)
        await message.answer("Регистрация прошла успешно", reply_markup=kb_main_menu.as_markup(resize_keyboard=True))