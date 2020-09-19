import os
from re import sub

import config


def main():
    for root, subdirs, files in os.walk(config.get_song_path()):
        for file in files:
            new_name = sub(' ', '_', file)
            if not file == new_name:
                os.rename(os.path.join(root, file), os.path.join(root, new_name))


if __name__ == "__main__":
    main()