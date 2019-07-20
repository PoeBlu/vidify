# Spotify Videoclips

A simple tool to show Youtube **videoclips** and **lyrics** for the currently playing Spotify songs with VLC.

![example](screenshots/screenshot.png)

## How to install

Download the latest [release](https://github.com/marioortizmanero/spotify-videoclips/releases). Uncompress the .tar.gz file and run inside the folder:

`python ./setup.py install`

*Note: you can add the --user flag to install it locally.*
*Also, it's based on DBus so it only works on Linux.*

### Manually:

Install the latest version of `youtube-dl`, `python-vlc` and `lyricwikia`. With pip:

* `pip install --user youtube-dl; pip install --user python-vlc; pip install --user lyricwikia`

Then you can execute the script with python as you like.

*Note that they're avaliable on the AUR too: [youtube-dl](https://www.archlinux.org/packages/community/any/youtube-dl/), [python-vlc](https://aur.archlinux.org/packages/python-vlc/)*.


## How to use

You can use these flags to modify the behavior of the program:

```
usage: spotify_videoclips.py [-h] [-d] [-n] [-f] [-a VLC_ARGS]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           turn on debug mode
  -n, --no-lyrics       do not display lyrics
  -f, --fullscreen      play videos in fullscreen mode
  -a VLC_ARGS, --args VLC_ARGS
                        other arguments used when opening VLC. Note that some
                        like --args='--fullscreen' won't work.
```

---

## Current limitations:
* Spotify doesn't currently (15/07/19) support the MPRIS property `Position` so the starting offset is calculated manually and may be a bit rough

## Documentation

Helpful documentation links for contributing:
* [DBus](https://dbus.freedesktop.org/doc/dbus-specification.html), [DBus official](https://dbus.freedesktop.org/doc/dbus-specification.html), [DBus python module](https://dbus.freedesktop.org/doc/dbus-python/tutorial.html)
* [MPRIS](https://specifications.freedesktop.org/mpris-spec/latest/Player_Interface.html#Property:Position)
* [python-vlc](https://www.olivieraubert.net/vlc/python-ctypes/doc/)
* [youtube-dl](https://github.com/ytdl-org/youtube-dl)

