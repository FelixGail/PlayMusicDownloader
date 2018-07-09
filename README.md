# PlayMusicDownloader

## Installation
Clone or download and extract [this project](https://github.com/FelixGail/PlayMusicDownloader/releases/latest)

###### Prerequisites
Python 3.5+ 

###### Dependencies
 - [colorama](https://github.com/tartley/colorama)
 - [gmusicapi](https://github.com/simon-weber/gmusicapi)
 - [mutagen](https://github.com/quodlibet/mutagen)
 

If you have `pip` installed simply run the following command:
```
sudo -H pip install -r requirements.txt --upgrade
```
Please note that `pip` is called `pip3` for python3.5 on some linux distributions.

## Configuration

The following options can be set:

option              | required  | default           | description
------              | --------  | -------           | -----------
gmusic_username     | yes       | -                 | the email connected with your google play subscription
device_id           | yes       | -                 | the id of an `android` or `ios` device connected with googleplay
gmusic_locale       | no        | system local      | the locale your account is registered in (e.g. en_US)
song_path           | no        | songs/            | os path the songs will be saved to
file_name_pattern   | no        | {artist}-{title}  | the pattern files will be created by. allowed tags: {artist}, {title}, {album}, {id} (GooglePlay song id [unique]). Forbidden characters will be removed (/ \ * ? : \| < > ").
quality             | no        | hi                | song quality. allowed values: lo, med, hi
save_album_cover    | no        | true              | download the album cover?
download_threads    | no        | 1                 | count of allowed parallel downloads

## Usage
Simply run the `main.py`. 
```
python3 main.py
```

## Errors and suggestions
Did you find a bug or have a suggestion? File an [issue](https://github.com/FelixGail/PlayMusicDownloader/issues).

