from colorama import Fore
from getpass import getpass
import json
import locale
import sys


def load_config():
    with open('config.json', 'r') as config_file:
        return json.loads(config_file.read())


def get_quality():
    return config.get('quality', 'hi')


def get_song_path():
    return config.get('song_path', 'songs/')


def get_username():
    username = config.get('gmusic_username', False)
    if not username:
        print(COLOR_ERROR+'username missing in config.json')
        sys.exit()
    return username


def get_device_id():
    device_id = config.get('device_id', False)
    if not device_id:
        print(COLOR_ERROR+'device_id missing in config.json')
        sys.exit()
    return device_id


def get_password():
    global password
    if not password:
        password = getpass('Enter Google-Play password: ')
    return password


def get_gmusic_locale():
    return config.get('gmusic_locale', locale.getdefaultlocale()[0])


def get_download_threads():
    return config.get('download_threads', 1)


def get_file_name_pattern():
    return config.get('file_name_pattern', '{artist}-{title}')


def get_save_album_cover():
    return config.get('save_album_cover', True)


password = False
config = load_config()
COLOR_ERROR = Fore.RED
COLOR_PERCENT = Fore.LIGHTGREEN_EX
COLOR_EXISTING = Fore.LIGHTBLACK_EX
COLOR_RESET = Fore.RESET