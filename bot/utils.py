from typing import Callable
from aiohttp import ClientSession
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_RESULT_LIMT = 10

class BotStates(StatesGroup):
    search_anime = State()

class SearchAnimeCallback(CallbackData, prefix='search_anime'):
    name: str
    offset: int = 0
    
class AnimeCallback(CallbackData, prefix='anime'):
    id: int
    mal_id: int | None

class ShowEpisodeCallback(CallbackData, prefix='show_episode'):
    anime_id: int
    offset: int = 0

class EpisodeCallback(CallbackData, prefix='episode'):
    id: int

async def send_request(
        *,
        api: ClientSession,
        endpoint: str,
        params: dict = {}
) -> list | dict | None:
    async with api.get(endpoint, params=params) as response:
        if response.ok:
            return await response.json()
    return None

def get_inline_back_next_keyboard(
        json: list[dict],
        main_callback: ShowEpisodeCallback | SearchAnimeCallback,
        callback_data: Callable,
        data_callback_key: tuple,
        text: str = '',
        dynamic_text_key: Callable = lambda data: ''
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=text+dynamic_text_key(data),
                callback_data=callback_data(**{key: data[key] for key in data_callback_key}).pack()
            )] for data in json
        ]
    )

    if len(json) == API_RESULT_LIMT:
        main_callback.offset += API_RESULT_LIMT
        keyboard.inline_keyboard.append([InlineKeyboardButton(
            text='Next',
            callback_data=main_callback.pack()
        )])
        main_callback.offset -= API_RESULT_LIMT

    if main_callback.offset > 0:
        main_callback.offset -= API_RESULT_LIMT
        keyboard.inline_keyboard[-1].append(InlineKeyboardButton(
            text='Back',
            callback_data=main_callback.pack()
        ))

    return keyboard