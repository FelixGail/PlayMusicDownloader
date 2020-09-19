import os
from re import sub

from mutagen.easyid3 import EasyID3

import config

EasyID3.RegisterTXXXKey('playlists', 'Google Play Playlist')


def main():
    for root, subdirs, files in os.walk(config.get_song_path()):
        for file in files:
            rel_filepath = file
            relpath = os.path.relpath(root, config.get_song_path())
            if not relpath == ".":
                rel_filepath = os.path.join(relpath, file)
            print(rel_filepath + ":")
            try:
                meta = EasyID3(os.path.join(root, file))
                if 'playlists' in meta:
                    for playlist in meta['playlists']:
                        print("\t->{}".format(playlist))
                        with open(os.path.join(config.get_song_path(), remove_forbidden_characters(playlist) + ".m3u"), 'a+') as p_file:
                            p_file.seek(0)
                            lines = p_file.read().splitlines()
                            if str(file) not in [elem.split('/')[-1] for elem in lines]:
                                p_file.write(rel_filepath)
                                p_file.write("\n")
                                print("\t\t-> writing to file")
                            else:
                                print("\t\t-> already in playlist")
            except Exception as e:
                print(e)


def remove_forbidden_characters(value):
    return sub('[<>?*/:|\\\"]', '', value)

if __name__ == '__main__':
    main()
