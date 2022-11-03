import requests as requests
from bs4 import BeautifulSoup
from animestream.parsers import common


def print_hi(name):
    response = requests.get("https://www.animeunity.tv/archivio", {'offset': 0})

    soup = BeautifulSoup(response.text, "html.parser")
    meta = soup.select_one('meta[name="csrf-token"]')
    print(meta)

    token = meta['content']

    print("DETECTED TOKEN")
    print(token)

    common.headers['x-csrf-token'] = token

    response = requests.post("https://www.animeunity.tv/archivio/get-animes", {'offset': 0}, headers=headers)
    print(response.text)
