import config
from gmusicapi.clients.mobileclient import Mobileclient
from gmusicapi.exceptions import CallFailure
import math
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen import id3
import os
from re import sub
import signal
import sys
import threading
from time import sleep
import urllib
import traceback


def wait_key():
    # Wait for a key press on the console and return it.
    if os.name == 'nt':
        import msvcrt
        while msvcrt.kbhit():
            return ord(msvcrt.getch())
    else:
        import termios
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            return ord(sys.stdin.read(1))
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)


def input_escape_or_return(message):
    print(message)
    while continue_event.is_set():
        c = wait_key()
        if c == 27:
            # Escape
            return False
        if c == 10 or c == 13:
            # Return
            return True


def remove_forbidden_characters(value):
    return sub('[<>?*/:|\\\"]', '', value)


def get_int_input(message, value_range=None):
    while 1 and continue_event.is_set():
        try:
            value = int(input(message))
            if value_range is not None and value not in value_range:
                continue
            return value
        except ValueError:
            pass
        except EOFError:
            sys.exit()


def collect_tracks(selected_playlist):
    global tracks
    global playlist_position_format
    if selected_playlist['type'] == 'SHARED':
        tracks = api.get_shared_playlist_contents(selected_playlist['shareToken'])
    else:
        all_user_playlists = api.get_all_user_playlist_contents()
        for p in all_user_playlists:
            if selected_playlist['id'] == p['id']:
                tracks_tmp = p['tracks']
                tracks = []
                for i in range(0,len(tracks_tmp)):
                    tracks.append((i+1, tracks_tmp[i]))
                playlist_position_format = '{:0>' + str(math.floor(math.log(len(tracks_tmp),10))+1) + '}'
                break


def add_to_meta(meta, info, meta_key, info_key=None):
    if info_key is None:
        info_key = meta_key
    if info.contains(info_key):
        meta[meta_key] = info.get(info_key)


class DownloadThread(threading.Thread):
    downloaded_tracks = None
    track_count = None

    def __init__(self, thread_id, playlist_name):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.assigned_song = None
        self.playlist_name = playlist_name
        self.initialize_class_vars()
        self.file_path = None

    def run(self):
        assign_lock_download.acquire()
        while len(tracks) > 0 and continue_event.is_set():
            self.assigned_song = tracks.pop(0)
            assign_lock_download.release()
            self.download()
            assign_lock_download.acquire()
        assign_lock_download.release()
        threads.remove(self)

    def download(self):
        position = self.assigned_song[0]
        song = self.assigned_song[1]
        song_id = song['trackId']

        if 'track' not in song:
            print('GMusicAPI does not support Information about self uploaded tracks. Skipping Song')
            return

        info = Decoder(song['track'], 'UTF-16')

        if(info.contains('totalTrackCount')):
            track_padding = '{:0>' + str(math.floor(math.log(int(info.get('totalTrackCount')),10))+1) + '}'
        else:
            track_padding = '{:0>2}'

        self.file_path = os.path.join(config.get_song_path(), config.get_file_name_pattern()
                                      .format(artist=remove_forbidden_characters(info.get('artist')),
                                              album=remove_forbidden_characters(info.get('album')),
                                              title=remove_forbidden_characters(info.get('title')),
                                              track_number=track_padding.format(info.get('trackNumber')),
                                              playlist_position=playlist_position_format.format(position),
                                              id=song_id)
                                      + ".mp3")

        if os.path.isfile(self.file_path):
            try:
                meta = EasyID3(self.file_path)
            except mutagen.id3.ID3NoHeaderError:
                meta = mutagen.File(self.file_path, easy=True)
                meta.add_tags()
            if 'playlists' not in meta:
                meta['playlists'] = [self.playlist_name]
            elif self.playlist_name not in meta['playlists']:
                meta['playlists'] += [self.playlist_name]
            meta.save(v1=2)
            class_var_lock.acquire()
            print("{}{:6} {}Song '{} by {}' already present in target directory.{}"
                  .format(config.COLOR_PERCENT, self.get_percent(), config.COLOR_EXISTING,
                          info.get('title'), info.get('artist'), config.COLOR_RESET))
            class_var_lock.release()
            return

        class_var_lock.acquire()
        print("{}{:6} {}Downloading song '{} by {}'"
              .format(config.COLOR_PERCENT, self.get_percent(),
                      config.COLOR_RESET, info.get('title'), info.get('artist')))
        class_var_lock.release()
        attempts = 3
        url = None

        while attempts and not url and continue_event.is_set():
            try:
                url = api.get_stream_url(song_id, quality=config.get_quality())
                if not url:
                    raise CallFailure("call returned None for song_id {}".format(song_id), "get_stream_url")
            except CallFailure:
                # Sometimes, the call returns a 403
                attempts -= 1
                if not attempts:
                    raise IOError("Can't download song from Google Play")
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("Unexpected error while trying to download. Joining thread.")
                traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
                self.join()


            request = urllib.request.Request(url)
            with urllib.request.urlopen(request) as page:
                with open(self.file_path, "wb") as file:
                    file.write(page.read())

        meta = mutagen.File(self.file_path, easy=True)
        meta.add_tags()
        add_to_meta(meta, info, 'title')
        add_to_meta(meta, info, 'artist')
        add_to_meta(meta, info, 'album')
        add_to_meta(meta, info, 'date', 'year')
        add_to_meta(meta, info, 'genre')
        add_to_meta(meta, info, 'tracknumber', 'trackNumber')
        add_to_meta(meta, info, 'length', 'durationMillis')

        meta['playlists'] = [self.playlist_name]

        if config.get_save_album_cover():
            try:
                art_request = urllib.request.Request(info.get('albumArtRef')[0]['url'])
                with urllib.request.urlopen(art_request) as page:
                    meta['albumArt'] = page.read()
            except (KeyError, IOError) as e:
                print(e)

        meta.save(v1=2)

    @classmethod
    def get_percent(cls):
        if cls.track_count > 0:
            percent = round((cls.downloaded_tracks / cls.track_count) * 100)
            cls.increase_downloaded_tracks()
            return '[{}%]'.format(percent)
        return 100

    @classmethod
    def initialize_class_vars(cls):
        class_var_lock.acquire()
        if cls.downloaded_tracks is None:
            cls.downloaded_tracks = 0
            cls.track_count = len(tracks)
        class_var_lock.release()

    @classmethod
    def increase_downloaded_tracks(cls):
        cls.downloaded_tracks += 1
        return cls.downloaded_tracks

    @classmethod
    def reset_class_vars(cls):
        cls.downloaded_tracks = None
        cls.track_count = None


class Decoder(object):
    def __init__(self, dictionary, encoding):
        self.encoding = encoding
        self.dictionary = dictionary

    def get(self, key):
        value = self.dictionary[key]
        if isinstance(value, str):
            return sub(u"(\u2018|\u2019)", "'", value)
        elif isinstance(value, int):
            return str(value)
        return value

    def contains(self, key):
        return key in self.dictionary

exitCalled = False


def signal_handler(signal, frame):
    global exitCalled
    if exitCalled:
        exit(1)
    exitCalled = True
    print('\n{}Exit signal detected. Shutting down gracefully{}\n'.format(config.COLOR_ERROR, config.COLOR_RESET))
    continue_event.clear()


def get_album_art(id3, _):
    return id3['APIC']


def set_album_art(id3, _, value):
    id3.add(mutagen.id3.APIC(1, '->', 3, u"Front Cover", value))


if not os.path.isdir(config.get_song_path()):
    os.makedirs(config.get_song_path())

EasyID3.RegisterTXXXKey('playlists', 'Google Play Playlist')
EasyID3.RegisterKey('albumArt', get_album_art, set_album_art)

api = None
try:
    continue_event = threading.Event()
    continue_event.set()
    signal.signal(signal.SIGINT, signal_handler)
    api = Mobileclient(debug_logging=False)
    if not api.login(config.get_username(), config.get_password(), config.get_device_id(), config.get_gmusic_locale()):
        print(config.COLOR_ERROR + "Could not log into GMusic")
        sys.exit()

    playlists = api.get_all_playlists()
    playlists_len = len(playlists)
    playlists_string_width = math.floor(math.log10(playlists_len)) + 1
    another_playlist = True
    assign_lock_download = threading.Lock()
    class_var_lock = threading.Lock()
    tracks = []
    while another_playlist and continue_event.is_set():
        print('\nA list of all playlists:\n')
        i = 0
        max_len = 0
        for playlist in playlists:
            print('{:>{count}}: {}'.format(i, playlist['name'], count=playlists_string_width))
            max_len = max(max_len, len(playlist['name']))
            if (i + 1) % 25 == 0 and i < playlists_len:
                if not input_escape_or_return('{:-^{width}}'.format('[ESC] to stop - [Return] for more',
                                                                    width=(max_len + playlists_string_width + 2))):
                    break
            i += 1
        selected_id = get_int_input('\nEnter a playlist id (0-{}): '.format(playlists_len - 1), range(0, playlists_len))
        print()
        playlist = playlists[selected_id]
        collect_tracks(playlist)
        threads = []
        for i in range(0, config.get_download_threads()):
            new_thread = DownloadThread(i, playlist['name'])
            threads.append(new_thread)
            new_thread.start()

        while len(threads) > 0:
            sleep(1)

        if continue_event.is_set():
            print('\n{}[100%]{} Finished Downloading!'.format(config.COLOR_PERCENT, config.COLOR_RESET))
            DownloadThread.reset_class_vars()
            another_playlist = input_escape_or_return('\n[Esc] to exit - [Return] to continue')

finally:
    if api is not None and api.is_authenticated():
        api.logout()
