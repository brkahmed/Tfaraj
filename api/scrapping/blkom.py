import asyncio
import json
import re
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from concurrent.futures import ProcessPoolExecutor
from functools import reduce
from operator import add
from collections import deque
from utils import get_logger, get_proxy

logger = get_logger('blkom')

async def main():
    await scrappe()

async def scrappe():
    async with ClientSession() as session:
        session.ua = UserAgent()

        #animes = await get_animes(session)

        #animes = await set_episodes_url(session, deque(animes))

        with open('result.json') as f:
            animes = json.load(f)

        return
        with open('result.json', 'w') as f:
            json.dump(animes, f)


async def get_animes(
    session: ClientSession,
    list_url: str = 'https://blkom.com/animes-list?sort_by=name&page={}',
    pages_number: int = 214    
) -> list[dict[str, str]]:
    urls = (list_url.format(i) for i in range(1, pages_number + 1))
    tasks = (get_page(session, url, 'LIST PAGE') for url in urls)
    pages = await asyncio.gather(*tasks)

    with ProcessPoolExecutor() as executor:
        result = reduce(add, executor.map(process_list_page, pages))

    return result

def process_list_page(page: str) -> list[dict[str, str]]:
    logger.info('LIST PAGE:PARSING:START')

    soup = BeautifulSoup(page, 'lxml')
    infos = map(
        lambda info: (info.select_one('.name a'), info.select_one('.story-text').text),
        soup.select('.info')
    )

    logger.info('LIST PAGE:PARSING:END')
    return [
        {
            'name': tag.text,
            'url': tag.attrs['href'],
            'story': story
        } for tag, story in infos
    ]
            
async def set_episodes_url(
        session: ClientSession,
        animes: deque[dict],
        pages_per_time: int = 200,
) -> list[dict]:
    urls = (anime['url'] for anime in animes)
    tasks = deque(get_page(session, url, 'EPISODE URL') for url in urls)
    result = []
    while tasks:
        avaible = min(pages_per_time, len(tasks))
        pages = await asyncio.gather(*(tasks.popleft() for _ in range(avaible)))
        with ProcessPoolExecutor() as executor:
            result.extend(executor.map(process_anime_page, pages, (animes.popleft() for _ in range(avaible))))

    return result

def process_anime_page(
        page: str,
        anime: dict,
        mal_id_pattern: re.Pattern = re.compile(r'/(\d+)/?')
) -> dict[str, str]:    
    logger.info('ANIME PAGE:PARSING:START:%s', anime['name'])
  
    try:
        soup = BeautifulSoup(page, 'lxml')
    except TypeError:
        logger.error('ANIME PAGE:PARSING:MISSING INFO:PAGE:%s', anime['name'])
        return anime
  
    try:
        mal_id = mal_id_pattern.search(soup.select_one('a.blue.cta').attrs['href']).group(1)
    except (KeyError, AttributeError):
        logger.warning('ANIME PAGE:PARSING:MISSING INFO:MAL_ID:%s', anime['name'])
        mal_id = None
  
    try:
        episode_urls = {tag.select_one('span:last-of-type').text:tag.attrs['href'] for tag in soup.select('.episode-link a')}
    except AttributeError as e:
        logger.warning('ANIME PAGE:PARSING:MISSING INFO:EPISODES:%s', anime['name'])
        episode_urls = None

    anime.update(
        mal_id=mal_id,
        episode_urls=episode_urls
    )

    logger.info('ANIME PAGE:PARSING:FINISHED:%s', anime['name'])
    return anime

async def set_sources_url(
        session: ClientSession,
        animes: list[dict],
        pages_per_time: int = 200,
) -> list[dict]:
    urls = (url for anime in animes for url in anime['episode_urls'])
    tasks = deque(get_page(session, url) for url in urls)
    result = []
    while tasks:
        avaible = min(pages_per_time, len(tasks))
        pages = await asyncio.gather(*(tasks.popleft() for _ in range(avaible)))
        with ProcessPoolExecutor() as executor:
            result.extend(executor.map(process_episode_page, pages))

    result = iter(result)
    for anime in animes:
        anime['episodes'] = {episode_number: next(result) for episode_number in anime['episodes_url'].keys()}

def process_episode_page(
        page: str,
        quality_pattern: re.Pattern = re.compile(r'\d+p?')
) -> dict[str, str]:
    logger.info('EPISODE PAGE:PARSING:START')

    soup = BeautifulSoup(page, 'lxml')
    embed = map(
        lambda tag: {tag.text: tag.attrs['href']},
        soup.select('.panel-body a')
    )
    download = map(
        lambda tag: {
            quality_pattern.search(tag.text).group():tag.attrs['href']
        },
        soup.select('.panel-body a')
    )

    logger.info('ANIME PAGE:PARSING:FINISHED')



async def get_page(
    session: ClientSession,
    url: str,
    log_msg: str,
    retry_attempts: int = 10,
    sleep_time: float = 1,
    proxy: str | None = None,
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
) -> str | None:
    while True:
        logger.info('%s:REQUEST:SENDING:%s', log_msg, url)
        try:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                if response.ok:
                    logger.info('%s:REQUEST:SUCCESS:%s', log_msg, url)
                    return await response.text()
                logger.info('%s:REQUEST:FAIL:%i:%s', log_msg, response.status, url)
        except Exception as e:
            logger.info('%s:REQUEST:FAIL:%s:%s', log_msg, str(e), url)

        if retry_attempts == 0: break
        retry_attempts -= 1

        headers['User-Agent'] = session.ua.random
        proxy = get_proxy()
        await asyncio.sleep(sleep_time)

    logger.error('%s:REQUEST:NOT SERVED:%s', log_msg, url)


if __name__ == '__main__':
    asyncio.run(main())