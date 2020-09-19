import os
from re import sub

from mutagen.easyid3 import EasyID3

import config

EasyID3.RegisterTXXXKey('playlists', 'Google Play Playlist')


def main():
    playlist_dict = {}
    for root, subdirs, files in os.walk(config.get_song_path()):
        for file in files:
            rel_filepath = file
            relpath = os.path.relpath(root, config.get_song_path())
            if not relpath == ".":
                rel_filepath = os.path.join(relpath, file)
            print(rel_filepath + ":")
            try:
                meta = EasyID3(os.path.join(root, file))
                print(meta)
                if 'playlists' in meta:
                    for playlist in meta['playlists']:
                        playlist_split = playlist.split(':')
                        print("\t->{}".format(playlist))
                        if playlist_split[0] in playlist_dict:
                            key = len(playlist_dict[playlist_split[0]])
                            if len(playlist_split) > 1:
                                key = int(playlist_split[1])
                            playlist_dict[playlist_split[0]][key] = rel_filepath
                        else:
                            key = 0
                            if len(playlist_split) > 1:
                                key = int(playlist_split[1])
                            playlist_dict[playlist_split[0]] = {key: rel_filepath}
                        print(playlist_dict)
            except Exception as e:
                print(e)
    for playlist in playlist_dict:
        print("writing playlist " + playlist)
        with open(os.path.join(config.get_song_path(), remove_forbidden_characters(playlist) + ".m3u"), 'a+') as p_file:
            p_file.seek(0)
            for playlist_key in sorted(playlist_dict[playlist]):
                playlist_item = playlist_dict[playlist][playlist_key]
                print("\t" + playlist_item)
                p_file.write(playlist_item)
                p_file.write("\n")
            p_file.truncate()



def remove_forbidden_characters(value):
    return sub(' ', '_', sub('[<>?*/:|\\\"]', '', value))

if __name__ == '__main__':
    main()
