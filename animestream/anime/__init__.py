from typing import List


class Episode:
    anime = None
    number = -1
    url = ''
    referer = ''

    def __init__(self, anime, number, url, referer, provider):
        self.anime = anime
        self.number = number
        self.url = url
        self.referer = referer
        self.provider = provider

    def __str__(self):
        return f'Episode {self.number} of {self.anime} ({self.url}, referer: {self.referer})'


class Anime:
    id = ''
    name = ''
    url = ''
    image = ''
    description = ''
    provider = ''
    episodes: List[Episode] = []

    def __init__(self, name, url, provider, id):
        self.name = name
        self.url = url
        self.provider = provider
        self.id = id

    def __str__(self):
        return f'Anime {self.name} on ({self.provider}) ({self.url})'
