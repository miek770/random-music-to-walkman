# random-music-to-walkman

Fill up a device (usb key, mp3 player, directory, etc.) with random music from a source directory.

This is the initial commit and more details will be added as I revise the script, which is fairly old now (and not very well structured).

## To Do List

- There's a problem with the syncing progression, which probably indicates that there will also be a problem with the device being full before the end of the transfer;
- I have added rstrip() to the clean() function, but haven't really tested it;
- Currently the songs are only sorted by artist, not by song name. They should be sorted by both.
