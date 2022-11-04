# Module: main
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Example video plugin that is compatible with Kodi 19.x "Matrix" and above
"""
import sys
from typing import Set, List
from urllib.parse import urlencode, parse_qsl

import xbmc
import xbmcgui
import xbmcplugin

from animestream.anime import Anime
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


animes: List[Anime] = []


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(_URL, urlencode(kwargs))


def play_video(url, referer=None):
    # Adding referer to the headers
    if referer is not None:
        url = url + '|Referer=' + referer

    # create a playable item with a path to play
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def show_anime_list(animes: List[Anime]):
    for anime in animes:
        anime = animesaturn.get_anime_details(anime)

        anime_item = xbmcgui.ListItem(anime.name)
        anime_item.setInfo('video', {
            'title': anime.name,
            'plot': anime.description,
            'mediatype': 'tvshow',
            'showlink': anime.name
        })
        anime_item.setArt({'poster': anime.image, 'banner': anime.image, 'thumb': anime.image})

        xbmcplugin.addDirectoryItem(
            handle=_HANDLE,
            url=get_url(action=Actions.LIST_EPISODES, anime=anime.id),
            listitem=anime_item,
            isFolder=True,
        )


def list_animes(page=0, size=10):
    xbmcplugin.setPluginCategory(_HANDLE, 'Anime')
    search_item = xbmcgui.ListItem(label='Cerca Anime:')
    xbmcplugin.addDirectoryItem(_HANDLE, get_url(action=Actions.ASK_SEARCH), search_item, True)

    global animes
    if len(animes) == 0:
        animes = animesaturn.get_anime_list()

    # get the correct animes for this page
    animes_page = animes[page * size:page * size + size]

    if page > 0:
        prev_item = xbmcgui.ListItem(label='Pagina Precedente')
        xbmcplugin.addDirectoryItem(_HANDLE, get_url(action=Actions.LIST_ANIMES, page=page - 1), prev_item, True)

    show_anime_list(animes_page)

    if len(animes) > (page + 1) * size:
        next_item = xbmcgui.ListItem(label='Pagina Successiva')
        xbmcplugin.addDirectoryItem(_HANDLE, get_url(action=Actions.LIST_ANIMES, page=page + 1), next_item, True)

    xbmcplugin.endOfDirectory(_HANDLE)


def list_episodes(anime_id):
    global animes
    # TODO: TROVA UN MODO DI SALVARE GLI ANIME IN MEMORIA PER NON DOVERLI RICARICARE OGNI VOLTA
    if len(animes) == 0:
        animes = animesaturn.get_anime_list()

    anime = list(filter(lambda x: x.id == anime_id, animes))[0]

    # get episodes and create list in folder
    anime = animesaturn.get_anime_details(anime)
    episodes = animesaturn.get_anime_episodes(anime)

    xbmcplugin.setPluginCategory(_HANDLE, anime.name)

    for episode in episodes:
        episode_item = xbmcgui.ListItem(anime.name + " Ep." + str(episode.number))
        episode_item.setProperty('IsPlayable', 'true')
        episode_item.setArt({'poster': anime.image, 'banner': anime.image, 'thumb': anime.image})
        episode_item.setInfo('video', {
            'title': anime.name + " Episodio " + str(episode.number),
            'plot': anime.description,
            'episode': episode.number,
            'showlink': anime.name,
            'mediatype': 'episode'
        })

        xbmcplugin.addDirectoryItem(
            handle=_HANDLE,
            url=get_url(action=Actions.PLAY, video=episode.url, referer=episode.referer),
            listitem=episode_item,
            isFolder=False,
        )

    xbmcplugin.endOfDirectory(_HANDLE)


def do_search(search_name):
    # search for anime
    global animes
    animes = animesaturn.get_anime_list()

    xbmcplugin.setPluginCategory(_HANDLE, search_name)

    xbmc.log("SEARCHING ANIME: " + search_name, xbmc.LOGWARNING)

    # filter the anime list
    found_animes = list(filter(lambda x: search_name.lower() in x.name.lower(), animes))

    xbmc.log("FOUND ANIME: " + str(len(found_animes)), xbmc.LOGWARNING)

    # show the back to list button
    back_item = xbmcgui.ListItem(label='Torna alla lista')
    xbmcplugin.addDirectoryItem(_HANDLE, get_url(action=Actions.LIST_ANIMES), back_item, True)

    if len(found_animes) > 0:
        show_anime_list(found_animes)
    else:
        no_anime_item = xbmcgui.ListItem(label='Nessun anime trovato')
        xbmcplugin.addDirectoryItem(_HANDLE, get_url(action=Actions.LIST_ANIMES), no_anime_item, True)

    xbmcplugin.endOfDirectory(_HANDLE)


def ask_search():
    # ask the user for the anime name to search
    anime_name = xbmcgui.Dialog().input('Cerca Anime:', type=xbmcgui.INPUT_ALPHANUM)
    if anime_name:
        if len(anime_name) > 3:
            do_search(anime_name)
        else:
            xbmcgui.Dialog().notification('Polpetta-Stream', 'Inserisci almeno 4 caratteri per la ricerca', xbmcgui.NOTIFICATION_ERROR, 5000)


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
            if 'page' in params:
                list_animes(int(params['page']))
            else:
                list_animes()

        elif params['action'] == Actions.PLAY:
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
    xbmc.log('CALLING PLUGIN')
    xbmc.log('PARAMS: {}'.format(sys.argv))
    router(sys.argv[2][1:])
