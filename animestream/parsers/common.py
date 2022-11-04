import requests
from requests.sessions import Session


def getSession() -> Session:
    out = requests.Session()
    out.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                                "AppleWebKit/537.36 (KHTML, like Gecko) " \
                                "Chrome/107.0.0.0 Safari/537.36 "
    return out
