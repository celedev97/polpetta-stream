import json
import os
import re
import time
from typing import List

import requests
import xbmc
from bs4 import BeautifulSoup

from animestream.anime import Anime, Episode, deserialize, serialize
from animestream.parsers import common


class AnimeSaturnDirect:
    _BASE_URL = 'https://www.animesaturn.in/'
    _PROVIDER = 'animesaturn'
    _session = common.getSession()

    def get_anime_list(self) -> List[Anime]:
        # LOADING ANIME ARCHIVE
        response = self._session.get(self._BASE_URL + 'animelistold?load_all=1')

        # GETTING ANIMES
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select('.list-group-item a')

        animes = []

        for element in elements:
            anime_url = element['href']
            anime_name = element.text.strip()
            anime_id = anime_url.split("/")[-1]

            animes.append(
                Anime(
                    id=anime_id,
                    name=anime_name,
                    url=anime_url,
                    provider=self._PROVIDER,
                )
            )

        return animes

    def get_anime_episodes(self, anime: Anime) -> List[Episode]:
        response = self._session.get(anime.url)

        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select('.episodi-link-button a')

        episodes = []

        for element in elements:
            episode_prepage_link = element['href']

            # region Parsing the Guarda lo Streaming page
            response = self._session.get(episode_prepage_link)

            soup = BeautifulSoup(response.text, 'html.parser')
            buttons = soup.select('a > .btn')
            button_watch = list(filter(lambda x: 'Guarda' in x.text, buttons))[0]
            referrer = button_watch.parent['href']
            # endregion

            response = self._session.get(referrer)

            video_url: str = ''

            soup = BeautifulSoup(response.text, 'html.parser')
            video = soup.select_one('video')

            if video is not None:
                if video.has_attr('src'):
                    video_url = video['src']
                else:
                    video_url = video.select_one('source')['src']

            if len(video_url) == 0 or video_url.startswith('blob'):
                # extract m3u8 url from jwplayer script tag
                scripts = soup.select('script')
                scripts_content = map(lambda x: str(x), scripts)
                jw_player_setup_script = list(filter(lambda x: 'jwplayer' in x and 'm3u8' in x, scripts_content))[0]
                video_url = re.search(r'"(.*m3u8)"', jw_player_setup_script).group(1)

            name = element.text.strip()

            episodes.append(
                Episode(
                    name=name.strip(),
                    url=video_url,
                    referer=referrer,
                    provider=self._PROVIDER
                )
            )

        anime.episodes = episodes
        return episodes

    def fetch_anime_details(self, anime: Anime, force=False):
        if anime.image is not None and force is False:
            return anime

        response = self._session.get(anime.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        image = soup.select_one('img.cover-anime')['src']
        description = soup.select_one('#shown-trama').text.strip()

        anime.image = image
        anime.description = description

        return anime


class AnimeSaturnCached(AnimeSaturnDirect):
    _cacheDir = '.'
    _direct: AnimeSaturnDirect

    _ANIME_LIST_CACHE_TIME = 3600 * 6  # 6 hours
    _ANIME_DETAIL_CACHE_TIME = 3600 * 24 * 15  # 15 days
    _ANIME_EPISODES_CACHE_TIME = 3600 * 6  # 6 hours

    def __init__(self, cache_dir='.', log=lambda x: None):
        self._cacheDir = cache_dir
        self._direct = AnimeSaturnDirect()
        self._log = log

    def get_anime_list(self) -> List[Anime]:
        cache_file = os.path.join(self._cacheDir, 'animes.json')

        if os.path.exists(cache_file):
            # reading cache to get the anime list if it's updated
            try:
                with open(cache_file, 'r') as f:
                    loaded = json.load(f)
                    last_update = loaded['last_update']

                    # check if it's past an hour from last update
                    if time.time() - last_update < self._ANIME_LIST_CACHE_TIME:
                        self._log('C_HIT, Cache anime trovata!')
                        return deserialize(loaded['animes'])
                    else:
                        self._log('C_OUT, Cache vecchia!')
            except:
                self._log('C_ERR, Cache anime trovata, ma non valida!')

        self._log('C_MIS, Scaricamento lista anime in corso...')

        output_animes = self._direct.get_anime_list()
        with open(cache_file, 'w') as f:
            anime_json = serialize(output_animes)
            json.dump({'animes': anime_json, 'last_update': time.time()}, f)
            self._log('C_SAV, Lista anime aggiornata!')

        return output_animes

    def fetch_anime_details(self, anime: Anime, force=False) -> Anime:
        if anime.image is not None and force is False:
            return anime

        details_dir = os.path.join(self._cacheDir, 'details')
        os.makedirs(details_dir, exist_ok=True)

        cache_file = os.path.join(details_dir, anime.id + '.json')

        if os.path.exists(cache_file):
            # reading cache to get the anime list if it's updated
            try:
                with open(cache_file, 'r') as f:
                    loaded = json.load(f)
                    last_update = loaded['last_update']

                    # check if it's past an hour from last update
                    if time.time() - last_update < self._ANIME_DETAIL_CACHE_TIME:
                        self._log('C_HIT, Cache dettagli trovata!')
                        return deserialize(loaded['anime'])
                    else:
                        self._log('C_OUT, Cache dettagli vecchia!')
            except:
                self._log('C_ERR, Cache dettagli trovata, ma non valida!')

        self._log('C_MIS, Scaricamento dettagli in corso...')

        output_anime = self._direct.fetch_anime_details(anime, force)
        with open(cache_file, 'w') as f:
            anime_json = serialize(output_anime)
            json.dump({'anime': anime_json, 'last_update': time.time()}, f)
            self._log('C_SAV, Anime aggiornato!')

        return output_anime

    def get_anime_episodes(self, anime: Anime) -> List[Episode]:
        cache_dir = os.path.join(self._cacheDir, 'episodes')
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, anime.id + '.json')

        if os.path.exists(cache_file):
            # reading cache to get the anime list if it's updated
            try:
                with open(cache_file, 'r') as f:
                    loaded = json.load(f)
                    last_update = loaded['last_update']

                    # check if it's past an hour from last update
                    if time.time() - last_update < self._ANIME_EPISODES_CACHE_TIME:
                        self._log('C_HIT, Cache episodi trovata!')
                        episodes: List[Episode] = deserialize(loaded['episodes'])
                        anime.episodes = episodes
                        return episodes
                    else:
                        self._log('C_OUT, Cache episodi vecchia!')
            except:
                self._log('C_ERR, Cache episodi trovata, ma non valida!')

        self._log('C_MIS, Scaricamento episodi in corso...')

        output_episodes = self._direct.get_anime_episodes(anime)
        with open(cache_file, 'w') as f:
            episodes_json = serialize(output_episodes)
            json.dump({'episodes': episodes_json, 'last_update': time.time()}, f)
            self._log('C_SAV, Episodi aggiornati!')

        anime.episodes = output_episodes
        return output_episodes

    def clear_episode_cache(self, anime_id):
        cache_dir = os.path.join(self._cacheDir, 'episodes')
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, anime_id + '.json')
        if os.path.exists(cache_file):
            os.remove(cache_file)

    def clear_anime_details_cache(self, anime_id):
        cache_dir = os.path.join(self._cacheDir, 'details')
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, anime_id + '.json')
        if os.path.exists(cache_file):
            os.remove(cache_file)

    def clear_anime_list_cache(self):
        cache_file = self._cacheDir + '/animes.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
