import re
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from animestream.anime import Anime, Episode
from animestream.parsers import common

BASE_URL = 'https://www.animesaturn.in/'
PROVIDER = 'animesaturn'


def get_anime_list() -> List[Anime]:
    driver = common.driver()

    # LOADING ANIME ARCHIVE
    driver.get(BASE_URL + 'animelistold')

    # WAITING FOR LOAD COMPLETE
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.list-group-item a'))
    )

    # GETTING ANIMES
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    elements = soup.select('.list-group-item a')

    animes = []

    for element in elements:
        url = element['href']
        name = element.text.strip()

        animes.append(
            Anime(name=name, url=url, provider='animesaturn')
        )

    return animes


def get_anime_episodes(anime: Anime) -> List[Episode]:
    driver = common.driver()
    driver.get(anime.url)

    # WAITING FOR LOAD COMPLETE
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.episodi-link-button'))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    elements = soup.select('.episodi-link-button a')

    episodes = []

    for element in elements:
        referrer = element['href']

        # region Parsing the Guarda lo Streaming page
        driver.get(referrer)
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.TAG_NAME, 'footer'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        buttons = soup.select('a > .btn')
        button_watch = list(filter(lambda x: 'Guarda' in x.text, buttons))[0]
        referrer = button_watch.parent['href']
        # endregion

        driver.get(referrer)
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.TAG_NAME, 'video'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
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
            Episode(anime=anime, number=number, url=video_url, referrer=referrer, provider=PROVIDER)
        )

    anime.episodes = episodes
    return episodes
