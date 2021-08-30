import os
import sys
from urllib.parse import parse_qsl
import urllib.parse
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon
from radiojavanapi import Client
from lib.search_history import SearchHistory
from lib.settings import Settings
from lib.vfs import VFS


# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

__addon__ = xbmcaddon.Addon()
home = __addon__.getAddonInfo('path')
addon_profile_path = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))

settings = Settings(__addon__)
vfs = VFS(addon_profile_path)
search_history = SearchHistory(settings, vfs)

# default icon and fanart
icon = xbmcvfs.translatePath(os.path.join(home, 'resources/icon.png'))
fanart = xbmcvfs.translatePath(os.path.join(home, 'resources/fanart.jpg'))

# Create RadioJavan client
rj_client = Client()
has_account = False


def set_credentials():
    global has_account

    use_account = settings.get('use.account')
    
    if use_account == 'true':
        # get username and password and do login with them
        username = settings.get('username')
        password = settings.get('password')

        try:
            rj_client.login(username, password)
            has_account = True
        except Exception as e:
            print('error in login: ' + str(e))
            pass


def get_user_input():  
    kb = xbmc.Keyboard('', 'Please enter search keyword')
    kb.doModal() # Onscreen keyboard appears
    if not kb.isConfirmed():
        return
    query = kb.getText() # User input
    return query


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urllib.parse.urlencode(kwargs))


def get_icon(name):
    return xbmcvfs.translatePath(os.path.join(home, 'resources/icon/' + name + '.png'))


def list_categories():
    """
    Create the list of categories
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'RadioJavan')
    
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'albums')

    add_live_streams()

    # Get plugin main categories
    categories = get_categories()

    for category in categories:
        list_item = xbmcgui.ListItem(label=category['name'])

        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        list_item.setArt({
                          'icon': category['image'],
                          'fanart': category['fanart']})
        
        # Set additional info for the list item.
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('music', {'title': category['name'],
                                    'mediatype': 'music'})
        
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.audio.example/?action=listing&category=Animals
        url = get_url(action='listing', 
            category_id=category['id'], category_name=category['name'], category_type=category['type'])
        
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    # Settings
    list_item = xbmcgui.ListItem(label='Settings')
    list_item.setArt({
                    'icon': get_icon('settings'),
                    'fanart': fanart})
    url = get_url(action='settings')
    xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    xbmcplugin.endOfDirectory(_handle)


def get_categories():
    music_icon = get_icon('music')
    search_icon = get_icon('search')

    categories = []

    categories.append({
        'id': 'search',
        'name': 'Search',
        'image': search_icon,
        'fanart': fanart,
        'type': 'music'
    })

    categories.append({
        'id': 'popular',
        'name': 'Popular Songs',
        'image': music_icon,
        'fanart': fanart,
        'type': 'music'
    })

    categories.append({
        'id': 'trending',
        'name': 'Trending Songs',
        'image': music_icon,
        'fanart': fanart,
        'type': 'music'
    })

    categories.append({
        'id': 'featured',
        'name': 'Featured Songs',
        'image': music_icon,
        'fanart': fanart,
        'type': 'music'
    })

    if has_account:
        categories.append({
            'id': 'my_music_playlists',
            'name': 'My Music Playlists',
            'image': get_icon('playlist_music'),
            'fanart': fanart,
            'type': 'music_playlist'
        })

        categories.append({
            'id': 'my_video_playlists',
            'name': 'My Video Playlists',
            'image': get_icon('playlist_video'),
            'fanart': fanart,
            'type': 'vide_playlist'
        })  

    return categories


def add_live_streams():
    tv_icon = get_icon('tv')
    radio_icon = get_icon('radio')

    # Add RadioJavan radio
    radio_stream = rj_client.get_radio_stream()

    list_item = xbmcgui.ListItem(label='RadioJavan Radio')
    
    list_item.setInfo('music', {'title': 'RadioJavan Radio',
                                'genre': 'radio',
                                'mediatype': 'music'})
    
    list_item.setArt({'thumb': radio_icon, 'icon': radio_icon, 'fanart': fanart})
    list_item.setProperty('IsPlayable', 'true')
    url = radio_stream['links']['hq']
    is_folder = False

    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add RadioJavan TV
    tv_stream = rj_client.get_tv_stream()

    list_item = xbmcgui.ListItem(label='RadioJavan TV')
    
    list_item.setInfo('video', {'title': 'RadioJavan TV',
                                'genre': 'tv',
                                'mediatype': 'video'})
    
    list_item.setArt({'thumb': tv_icon, 'icon': tv_icon, 'fanart': fanart})
    list_item.setProperty('IsPlayable', 'true')
    url = tv_stream
    is_folder = False

    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)


def list_searchs():
    xbmcplugin.setPluginCategory(_handle, 'RadioJavan')
    xbmcplugin.setContent(_handle, 'musics')

    # New search
    list_item = xbmcgui.ListItem(label='[B]New Search[/B]')
    url = get_url(action='search', opt='new', query='none')

    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Search history
    history = search_history.get()
    for k in sorted(list(history), reverse=True):
        history_query = history[k].get('query')
        list_item = xbmcgui.ListItem(label=history_query)
        url = get_url(action='search', opt='search', query=history_query)
        
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    
    xbmcplugin.endOfDirectory(_handle)


def do_search(query, opt):
    xbmcplugin.setPluginCategory(_handle, 'RadioJavan')
    xbmcplugin.setContent(_handle, 'musics')

    if opt == 'new':
        query = get_user_input()
        if not query:
            return []
        search_history.add(query)
    
    search_result = rj_client.search(query)

    for music in search_result.songs:
        list_item = xbmcgui.ListItem(label=music.name + ' - ' + music.artist)

        list_item.setInfo('music', {'title': music.name + ' - ' + music.artist,
                                    'genre': query,
                                    'mediatype': 'music'})

        list_item.setArt(
            {'thumb': music.photo, 'icon': music.photo, 'fanart': music.photo_player})
        
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')

        url = get_url(action='play', item_id=music.id, item_type='music')

        is_folder = False
        
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    xbmcplugin.endOfDirectory(_handle)


def list_my_music_playlists():
    xbmcplugin.setPluginCategory(_handle, 'RadioJavan')
    xbmcplugin.setContent(_handle, 'albums')

    # Get user music playlists
    all_playlists = rj_client.my_playlists()
    playlists = all_playlists.music_playlists

    for playlist in playlists:
        list_item = xbmcgui.ListItem(label=playlist.title)

        list_item.setArt({
                          'icon': playlist.photo,
                          'fanart': playlist.photo})

        list_item.setInfo('music', {'title': playlist.title,
                                    'mediatype': 'music'})

        url = get_url(
            action='listing', category_id=playlist.id, category_name=playlist.title, category_type='music_playlist')
        
        is_folder = True

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    xbmcplugin.endOfDirectory(_handle)

def list_my_video_playlists():
    xbmcplugin.setPluginCategory(_handle, 'RadioJavan')
    xbmcplugin.setContent(_handle, 'albums')

    # Get user music playlists
    all_playlists = rj_client.my_playlists()
    playlists = all_playlists.video_playlists

    for playlist in playlists:
        list_item = xbmcgui.ListItem(label=playlist.title)

        list_item.setArt({
                          'icon': playlist.photo,
                          'fanart': playlist.photo})

        list_item.setInfo('video', {'title': playlist.title,
                                    'mediatype': 'video'})

        url = get_url(
            action='listing', category_id=playlist.id, category_name=playlist.title, category_type='music_playlist')
        
        is_folder = True

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    xbmcplugin.endOfDirectory(_handle)


def list_items(category_id, category_name, type):
    xbmcplugin.setPluginCategory(_handle, category_name)
    xbmcplugin.setContent(_handle, 'musics')

    items = get_items(category_id, type)

    if type == 'video_playlist':
        add_videos(items, category_name)
    else:
        add_musics(items, category_name)

    xbmcplugin.endOfDirectory(_handle)


def get_items(category_id, type):
    if category_id == 'popular':
        return rj_client.get_popular_songs()
    elif category_id == 'trending':
        return rj_client.get_trending_songs()
    elif category_id == 'featured':
        return rj_client.get_featured_songs()
    elif type == 'music_playlist':
        return rj_client.get_music_playlist_by_id(category_id).songs
    elif type == 'video_playlist':
        return rj_client.get_video_playlist_by_id(category_id).videos


def add_musics(musics, category_name):
    for music in musics:
        list_item = xbmcgui.ListItem(label=music.name + ' - ' + music.artist)

        list_item.setInfo('music', {'title': music.name + ' - ' + music.artist,
                                    'genre': category_name,
                                    'mediatype': 'music'})

        list_item.setArt(
            {'thumb': music.photo, 'icon': music.photo, 'fanart': music.photo_player})
        
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')

        #url = get_url(action='play', item_id=music.id, item_type='music')
        url = music.hls_link

        is_folder = False
        
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

def add_videos(videos, category_name):
    for video in videos:
        list_item = xbmcgui.ListItem(label=video.name + ' - ' + video.artist)

        list_item.setInfo('video', {'title': video.name + ' - ' + video.artist,
                                    'genre': category_name,
                                    'mediatype': 'video'})

        list_item.setArt(
            {'thumb': video.photo, 'icon': video.photo, 'fanart': video.photo})
        
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')

        #url = get_url(action='play', , item_id=video.id, item_type='video')
        url = video.hq_hls

        is_folder = False
        
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)


def play_item(item_id, type):
    """
    Play an item by provided ID and type.
    """
    if type == 'video':
        item = rj_client.get_video_by_id(item_id)
    else:
        item = rj_client.get_song_by_id(item_id)
    
    item_art = {'thumb': item.photo, 
                'icon': item.photo, 
                'fanart': item.photo_player}
    
    if type == 'video':
        item_info=[
            {'video':[
                {'genre': item.artist},
                {'playcount': item.views}]
            }]
        
        playable_link = item.hq_link
    else:
        item_info=[
            {'music':[
                {'genre': item.artist},
                {'playcount': item.plays},
                {'duration': item.duration}]
            }]
        
        playable_link = item.hls_link
    
    if playable_link != None:
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=playable_link)
        
        play_item.setArt(item_art)
        play_item.setInfo(type, item_info)

        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


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
    print('parameters='+paramstring)
    
    if params:
        if params['action'] == 'listing':
            if params['category_id'] == 'search':
                list_searchs()
            elif params['category_id'] == 'my_music_playlists':
                list_my_music_playlists()
            elif params['category_id'] == 'my_video_playlists':
                list_my_video_playlists()
            else:
                list_items(params['category_id'], params['category_name'], params['category_type'])
        
        elif params['action'] == 'search':
            do_search(params['query'], params['opt'])
        
        elif params['action'] == 'play':
            play_item(params['item_id'], params['item_type'])
        
        elif params['action'] == 'clear.search.history':
            vfs.destroy()
            dialog = xbmcgui.Dialog()
            dialog.ok('RadioJavan', 'Search history cleared')
        
        elif params['action'] == 'settings':
            __addon__.openSettings()
        
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    # login account
    set_credentials()

    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
