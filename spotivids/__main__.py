import sys
import time
import logging
from typing import Callable, Union

import youtube_dl
import lyricwikia
from PySide2.QtWidgets import QApplication, QMainWindow

from .config import Config
from .utils import stderr_redirected, ConnectionNotReady
from .gui import MainWindow


# Cross platform info
BSD = sys.platform.find('bsd') != -1
LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WINDOWS = sys.platform.startswith('win')

# Initialization and parsing of the config from arguments and config file
config = Config()
config.parse()

# Logger initialzation with precise milliseconds handler
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)
level = logging.DEBUG if config.debug else logging.ERROR
logger.setLevel(level)

# Youtube-dl config
ydl_opts = {
    'format': 'bestvideo',
    'quiet': not config.debug
}
if config.max_width is not None:
    ydl_opts['format'] += f"[width<={config.max_width}]"
if config.max_height is not None:
    ydl_opts['format'] += f"[height<={config.max_height}]"


def format_name(artist: str, title: str) -> str:
    """
    Some local songs may not have an artist name so the formatting
    has to be different.
    """

    return title if artist in (None, '') else f"{artist} - {title}"


def get_url(artist: str, title: str) -> str:
    """
    Getting the youtube direct link with youtube-dl.
    """

    name = f"ytsearch:{format_name(artist, title)} Official Video"

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(name, download=False)

    return info['entries'][0]['url']


def print_lyrics(artist: str, title: str) -> None:
    """
    Using lyricwikia to get lyrics.

    Colors are not displayed on Windows because it doesn't support ANSI
    escape codes and importing colorama isn't worth it currently.
    """

    name = format_name(artist, title)

    if WINDOWS:
        print(f">> {name}")
    else:
        print(f"\033[4m{name}\033[0m")

    try:
        print(lyricwikia.get_lyrics(artist, title) + "\n")
    except (lyricwikia.LyricsNotFound, AttributeError):
        print("No lyrics found\n")


def play_videos_linux(player: Union['VLCPlayer', 'MpvPlayer']) -> None:
    """
    Playing videos with the DBus API (Linux).

    Spotify doesn't currently support the MPRIS property `Position`
    so the starting offset is calculated manually and may be a bit rough.

    After playing the video, the player waits for DBus events like
    pausing the video.
    """

    from .api.linux import DBusAPI
    spotify = DBusAPI(player, logger)

    msg = "Waiting for a Spotify session to be ready..."
    if not wait_for_connection(spotify.connect, msg):
        return

    while True:
        start_time = time.time_ns()

        url = get_url(spotify.artist, spotify.title)
        is_playing = spotify.is_playing
        player.start_video(url, is_playing)

        # Waits until the player starts the video to set the offset
        if is_playing:
            while player.position == 0:
                pass
            offset = int((time.time_ns() - start_time) / 10**9)
            player.position = offset
            logging.info(f"Starting offset is {offset}")

        if config.lyrics:
            print_lyrics(spotify.artist, spotify.title)

        spotify.wait()


def play_videos_swspotify(player: Union['VLCPlayer', 'MpvPlayer']) -> None:
    """
    Playing videos with the SwSpotify API (macOS and Windows).
    """

    from .api.swspotify import SwSpotifyAPI
    spotify = SwSpotifyAPI(logger)

    msg = "Waiting for a Spotify session to be ready..."
    if not wait_for_connection(spotify.connect, msg):
        return

    while True:
        start_time = time.time_ns()
        url = get_url(spotify.artist, spotify.title)
        player.start_video(url)

        # Waits until the player starts the video to set the offset
        while player.position == 0:
            pass
        offset = int((time.time_ns() - start_time) / 10**9)
        player.position = offset
        logging.debug(f"Starting offset is {offset}")

        if config.lyrics:
            print_lyrics(spotify.artist, spotify.title)

        spotify.wait()


def play_videos_web(player: Union['VLCPlayer', 'MpvPlayer']) -> None:
    """
    Playing videos with the Web API (optional).

    Unlike the other APIs, the position can be requested and the video is
    synced easily.
    """

    from .api.web import WebAPI
    spotify = WebAPI(player, logger, config.client_id,
                     config.client_secret, config.redirect_uri,
                     config.auth_token, config.expiration)

    msg = "Waiting for a Spotify song to play..."
    if not wait_for_connection(spotify.connect, msg):
        return

    # Saves the auth token inside the config file for future usage
    config.write_file('WebAPI', 'client_secret',
                      spotify._client_secret)
    config.write_file('WebAPI', 'client_id',
                      spotify._client_id)
    if spotify._redirect_uri != config._options.redirect_uri.default:
        config.write_file('WebAPI', 'redirect_uri',
                          spotify._redirect_uri)
    config.write_file('WebAPI', 'auth_token',
                      spotify._token.access_token)
    config.write_file('WebAPI', 'expiration',
                      spotify._token.expires_at)

    while True:
        url = get_url(spotify.artist, spotify.title)
        player.start_video(url, spotify.is_playing)

        offset = spotify.position
        player.position = offset

        if config.lyrics:
            print_lyrics(spotify.artist, spotify.title)

        spotify.wait()


def wait_for_connection(connect: Callable, msg: str,
                        attempts: int = 30) -> bool:
    """
    Waits for a Spotify session to be opened or for a song to play.
    Times out after `attempts` seconds to avoid infinite loops or
    too many API/process requests.

    Returns True if the connection was succesfull and False otherwise.
    """

    counter = 0
    while counter < attempts:
        try:
            connect()
        except ConnectionNotReady:
            if counter == 0:
                print(msg)
            counter += 1
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        else:
            return True
    else:
        print("Timed out")

    return False


def choose_platform() -> None:
    """
    Chooses a platform and player and starts the corresponding API function.
    """

    app = QApplication()
    if config.use_mpv:
        from .player.mpv import MpvPlayer
        player = MpvPlayer(logger, config.mpv_flags, config.fullscreen)
    else:
        from .player.vlc import VLCPlayer
        player = VLCPlayer(logger, config.vlc_args, config.fullscreen)
    window = MainWindow(player)
    window.show()

    if (BSD or LINUX) and not config.use_web_api:
        play_videos_linux(player)
    elif (WINDOWS or MACOS) and not config.use_web_api:
        play_videos_swspotify(player)
    else:
        play_videos_web(player)

    sys.exit(app.exec_())


def main() -> None:
    """
    Redirects stderr to /dev/null if debug is turned off, since
    sometimes VLC will throw non-fatal errors even when configured
    to be quiet.
    """

    if config.debug:
        choose_platform()
    else:
        with stderr_redirected():
            choose_platform()


if __name__ == '__main__':
    main()