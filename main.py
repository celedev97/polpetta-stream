# Module: main
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Example video plugin that is compatible with Kodi 19.x "Matrix" and above
"""
import sys
from typing import Set
from urllib.parse import urlencode, parse_qsl
import xbmcgui
import xbmcplugin

from animestream.parsers import animesaturn

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.
_HANDLE = int(sys.argv[1])


# Declare an enum for actions
class Actions:
    LIST_ANIMES = 'list_animes'
    LIST_EPISODES = 'list_episodes'
    PLAY = 'play'
    ASK_SEARCH = 'ask_search'
    DO_SEARCH = 'search'



def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(_URL, urlencode(kwargs))


def play_video(path, referer):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def list_animes():
    xbmcplugin.setPluginCategory(_HANDLE, 'Anime')
    search_item = xbmcgui.ListItem(label='Cerca Anime:')
    xbmcplugin.addDirectoryItem(_HANDLE, get_url(action=Actions.ASK_SEARCH), search_item, True)

    for anime in animesaturn.get_anime_list():
        anime_item = xbmcgui.ListItem(anime.name)
        xbmcplugin.addDirectoryItem(
            handle=_HANDLE,
            url=get_url(action='list_episodes', anime=anime.url),
            listitem=anime_item,
            isFolder=True,
        )

    xbmcplugin.endOfDirectory(_HANDLE)


def do_search(anime_name):
    pass


def ask_search():
    #ask the user for the anime name to search
    anime_name = xbmcgui.Dialog().input('Cerca Anime:', type=xbmcgui.INPUT_ALPHANUM)
    if anime_name:
        do_search(anime_name)


def list_episodes(param):
    pass


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == Actions.LIST_ANIMES:
            list_animes()
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'], params['referer'])
        elif params['action'] == Actions.LIST_EPISODES:
            list_episodes(params['anime'])
        elif params['action'] == Actions.ASK_SEARCH:
            ask_search()
        elif params['action'] == Actions.DO_SEARCH:
            do_search(params['query'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_animes()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
