from getpass import getpass
import json
import locale


def load_config():
    with open('config.json', 'r') as config_file:
        return json.loads(config_file.read())

config = load_config()


def get_quality():
    return config.get('quality', 'hi')


def get_song_path():
    return config.get('song_path', 'songs/')


def get_username():
    username = config.get('gmusic_username', False)
    if not username:
        raise ValueError('username missing in config.json')
    return username


def get_device_id():
    device_id = config.get('device_id', False)
    if not device_id:
        raise ValueError('device_id missing in config.json')
    return device_id

password = False


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
