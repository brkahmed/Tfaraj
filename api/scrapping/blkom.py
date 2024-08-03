import asyncio
import logging
import json
import re
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
from functools import reduce
from operator import add

logger = logging.Logger(__name__)

async def main():
    logger.addHandler(logging.StreamHandler())

    await scrappe()

async def scrappe():
    session = ClientSession()
    
    """ animes = await get_animes(session) """

    with open('result.json') as f:
        animes = json.load(f)

    set_episodes_url(session, animes)

    """ with open('result.json', 'w') as f:
        json.dump(animes, f) """

    await session.close()


async def get_animes(
    session: ClientSession,
    list_url: str = 'https://blkom.com/animes-list?sort_by=name&page={}',
    pages_number: int = 214    
):
    urls = (list_url.format(i) for i in range(1, pages_number + 1))
    tasks = (get_page(session, url) for url in urls)
    pages = await asyncio.gather(*tasks)
    logger.info('Parsing Anime Pages')
    with ProcessPoolExecutor() as executor:
        animes = reduce(add, executor.map(process_list_page, pages))
    return animes

def process_list_page(page: str):
    soup = BeautifulSoup(page, 'lxml')
    infos = map(
        lambda info: (info.select_one('.name a'), info.select_one('.story-text').text),
        soup.select('.info')
    )

    return [
        {
            'name': name.text,
            'url': name.attrs['href'],
            'story': story
        } for name, story in infos
    ]
            

async def set_episodes_url(
        session: ClientSession,
        animes: list[dict],
        mal_id_pattern: re.Pattern = re.compile(r'/(\d+)/')
):
    pass

async def get_page(
    session: ClientSession,
    url: str,
    retry_attempts: int = 10,
    headers: dict = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
    }
) -> str | None:
    while True:
        logger.info('SENDING REQUEST: %s', url)
        async with session.get(url, headers=headers) as response:
            if response.ok:
                return await response.text()
        
        logger.info('REQUEST FAIL: retrying %s', url)

        if retry_attempts == 0: break
        retry_attempts -= 1
        await asyncio.sleep(.5)


if __name__ == '__main__':
    asyncio.run(main())