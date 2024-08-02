import os
import asyncio
import logging
import sys
from dotenv import load_dotenv
from aiohttp import ClientSession
from utils import *

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.utils import markdown as md
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

async def main():
    load_dotenv()
    BOT_API_KEY = os.getenv('BOT_API_KEY')
    assert BOT_API_KEY, 'Failed to find bot api key'

    ANIME_API_URL = 'https://tfaraj.onrender.com/'
    
    JIKAN_API_URL = 'https://api.jikan.moe/'


    bot = Bot(BOT_API_KEY)
    dp.api = ClientSession(ANIME_API_URL)
    dp.jikan = ClientSession(JIKAN_API_URL)

    await dp.start_polling(bot)
    await dp.api.close()
    await dp.jikan.close()

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        text=f"Hello, {message.from_user.full_name}!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='البحث عن انمي 🔍')],
                [KeyboardButton(text='آخر الحلقات المضافة')],
                [KeyboardButton(text='أفضل الأنميات')]
            ],
        resize_keyboard=True
        )
    )
    
@dp.message(lambda message: message.text == 'البحث عن انمي 🔍')
async def ask_for_anime_name(message: Message, state: FSMContext):
    await state.set_state(BotStates.search_anime)
    await message.answer(f"ادخل اسم الانمي: ")

@dp.message(BotStates.search_anime)
async def search_anime(message: Message, state: FSMContext):
    await state.clear()

    json = await send_request(
        api=dp.api,
        endpoint='/anime',
        params={'name': message.text}
    )

    keyboard = [[InlineKeyboardButton(text=anime['name'], 
            callback_data=AnimeCallback(id=anime['id'], mal_id=anime['mal_id']).pack())] for anime in json]
    
    await message.answer(
        text=f'{md.bold("Founded Animes")}',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

@dp.callback_query(AnimeCallback.filter())
async def show_anime(query: CallbackQuery, callback_data: AnimeCallback):
    json = (await send_request(
        api=dp.jikan,
        endpoint=f'/v4/anime/{callback_data.mal_id}'
    ))['data']

    await query.message.answer_photo(json['images']['jpg']['large_image_url'])

    await query.message.answer(
        text=f'''{md.bold(json['title'])}
Score: {json['score']}⭐ - {json['scored_by']}
Rank: {json['rank']}''',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text='Show episodes',
                    callback_data=ShowEpisodeCallback(anime_id=callback_data.id).pack()
                )],
                [InlineKeyboardButton(
                    text='trailer',
                    url=json['trailer']['url']
                )]
            ]
        )
    )

@dp.callback_query(ShowEpisodeCallback.filter())
async def show_episode(query: CallbackQuery, callback_data: ShowEpisodeCallback):
    json = await send_request(
        api=dp.api,
        endpoint='/episode',
        params={'anime_id': callback_data.anime_id, 'offset': callback_data.offset}
    )

    keyboard = get_inline_back_next_keyboard(
        json,
        callback_data,
        EpisodeCallback,
        ('id',),
        'Episode ',
        lambda data: str(data['number'])
    )

    await query.message.answer(
        f'Show episode: {callback_data.anime_id} - {callback_data.offset}',
        reply_markup=keyboard
    )

@dp.callback_query(EpisodeCallback.filter())
async def show_sources(query: CallbackQuery, callback_data: EpisodeCallback):
    json = await send_request(
        api=dp.api,
        endpoint='/source',
        params={'episode_id': callback_data.id}
    )
    await query.message.answer(
        text=md.bold('Avaible sources'),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=source['name'],
                    url=source['url']
                )] for source in json if source['url'].startswith('http')
            ]
        )
    )



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
