import json
from typing import List
import inspect


class Episode(object):
    name = "-1"
    url = ''
    referer = ''

    def __init__(self, name, url, referer, provider):
        self.name = name
        self.url = url
        self.referer = referer
        self.provider = provider

    def __str__(self):
        return f'Episode: {self.name} ({self.url}, referer: {self.referer})'


class Anime(object):
    id = ''
    name = ''
    url = ''
    image = ''
    description = ''
    provider = ''
    episodes: List[Episode] = []

    def __init__(self, id, name, url, provider, image=None, description=None, **kwargs):
        self.name = name
        self.url = url
        self.provider = provider
        self.id = id
        self.image = image
        self.description = description
        self.episodes = []

    def __str__(self):
        return f'Anime {self.name} on ({self.provider}) ({self.url})'


def serialize(data):
    # check if it's an array
    if isinstance(data, list):
        return [serialize(x) for x in data]

    # check if it's a dict
    if isinstance(data, dict):
        return {k: serialize(v) for k, v in data.items()}

    # check if it's a class (a string is also a class sadly sooooo weird stuff)
    if hasattr(data, '__dict__'):
        return {k: serialize(v) for k, v in vars(data).items()}

    return data


animeKeys = vars(Anime('', '', '', '', '', '')).keys()


def deserialize(data):
    if isinstance(data, list):
        return [deserialize(x) for x in data]

    if isinstance(data, dict):
        # check if it's an anime
        if all(k in data.keys() for k in animeKeys):
            return Anime(**{k: deserialize(v) for k, v in data.items()})

        # check if it's an episode
        if all(k in data.keys() for k in vars(Episode('', '', '', '')).keys()):
            return Episode(**{k: deserialize(v) for k, v in data.items()})

        return {k: deserialize(v) for k, v in data.items()}

    return data
