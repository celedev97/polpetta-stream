import re
from typing import List

import requests
from bs4 import BeautifulSoup

from animestream.anime import Anime, Episode
from animestream.parsers import common

BASE_URL = 'https://www.animesaturn.in/'
PROVIDER = 'animesaturn'

session = common.getSession()


def get_anime_list() -> List[Anime]:
    # LOADING ANIME ARCHIVE
    response = session.get(BASE_URL + 'animelistold?load_all=1')

    # GETTING ANIMES
    soup = BeautifulSoup(response.text, 'html.parser')
    elements = soup.select('.list-group-item a')

    animes = []

    for element in elements:
        url = element['href']
        name = element.text.strip()
        id = url.split("/")[-1]

        animes.append(
            Anime(name=name,
                  url=url,
                  provider='animesaturn',
                  id=id,
                  )
        )

    return animes


def get_anime_episodes(anime: Anime) -> List[Episode]:
    response = session.get(anime.url)

    soup = BeautifulSoup(response.text, 'html.parser')
    elements = soup.select('.episodi-link-button a')

    episodes = []

    for element in elements:
        referrer = element['href']

        # region Parsing the Guarda lo Streaming page
        response = session.get(referrer)

        soup = BeautifulSoup(response.text, 'html.parser')
        buttons = soup.select('a > .btn')
        button_watch = list(filter(lambda x: 'Guarda' in x.text, buttons))[0]
        referrer = button_watch.parent['href']
        # endregion

        response = session.get(referrer)

        soup = BeautifulSoup(response.text, 'html.parser')
        video = soup.select_one('video')
        video_url = ''

        if video.has_attr('src'):
            video_url = video['src']
        else:
            video_url = video.select_one('source')['src']

        if video_url.startswith('blob'):
            # extract m3u8 url from jwplayer script tag
            scripts = soup.select('script')
            scripts_content = map(lambda x: str(x), scripts)
            jw_player_setup_script = list(filter(lambda x: 'jwplayer' in x and 'm3u8' in x, scripts_content))[0]
            video_url = re.search(r'"(.*m3u8)"', jw_player_setup_script).group(1)

        number = int(re.findall('(\\d+)', element.text)[0])

        episodes.append(
            Episode(anime=anime, number=number, url=video_url, referer=referrer, provider=PROVIDER)
        )

    anime.episodes = episodes
    return episodes


def get_anime_details(anime: Anime):
    response = session.get(anime.url)

    soup = BeautifulSoup(response.text, 'html.parser')
    image = soup.select_one('img.cover-anime')['src']
    description = soup.select_one('#shown-trama').text.strip()

    anime.image = image
    anime.description = description

    return anime