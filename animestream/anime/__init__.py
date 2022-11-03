from typing import List


class Episode:
    anime = None
    number = -1
    url = ''
    referrer = ''

    def __init__(self, anime, number, url, referrer, provider):
        self.anime = anime
        self.number = number
        self.url = url
        self.referrer = referrer
        self.provider = provider

    def __str__(self):
        return f'Episode {self.number} of {self.anime} ({self.url}, referer: {self.referrer})'


class Anime:
    id = ''
    name = ''
    url = ''
    image = ''
    description = ''
    provider = ''
    episodes: List[Episode] = []

    def __init__(self, name, url, provider):
        self.name = name
        self.url = url
        self.provider = provider

    def __str__(self):
        return f'Anime {self.name} on ({self.provider}) ({self.url})'
