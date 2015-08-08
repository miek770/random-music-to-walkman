#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys, os, random
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import mutagen.id3
from optparse import OptionParser
from mutagen.mp3 import HeaderNotFoundError

#==============================================================================
# Function:    player_is_mounted
# Description: Returns whether or not dest_path is mounted.
#==============================================================================
def player_is_mounted(path):
    return (os.popen("mount | awk '{print $3}' | grep " + path).read().replace("\n", "") == path)

#==============================================================================
# Function:    get_free_space
# Description: Returns the # of bytes avail on the player.
#==============================================================================
def get_free_space(path):
    return int(os.popen("df -B 1 | grep `mount | grep " + path + " | awk '{print $1}'`" + " | awk '{print $4}'").read().replace("\n", ""))

#==============================================================================
# Function:    get_file_size
# Description: Returns the # of bytes of a given file name.
#==============================================================================
def get_file_size(filename):
    return int(os.popen("ls -l \"" + filename + "\" | awk '{print $5}'").read().replace("\n", ""))

#==============================================================================
# Function:    main
# Description: Main routine. 
#==============================================================================
def main():
    # Options and arguments definition
    usage = 'usage: %prog [OPTION]... [SOURCE] [DEST]'
    parser = OptionParser(usage=usage)
    parser.add_option('-t',
                      '--threshold',
                      dest='threshold',
                      action='store',
                      help='Set the size threshold in byte at which the script stops copying (default=5000000)')
    (options, args) = parser.parse_args()

    # Options handling
    if options.threshold:
        threshold = options.threshold
    else:
        # When the player only has 5 megs left, we'll stop trying to copy. You
        # can lower this to 0 (or anything) so it will try to fit every song in
        # your collection, but consider the player might have 2 bytes left and
        # you have 800000 songs...
        threshold = 5000000

    # Arguments handling
    if len(args) != 2:
        print 'You have to specify a source (where your music files are stored) and a destination.'
        sys.exit()
    src_path = os.path.join(args[0])
    dest_path = os.path.join(args[1])

    print 'Random music to walkman'
    print '  Looking for the mp3 player...'
    if (not player_is_mounted(dest_path)):
        print 'Your mp3 player needs to be mounted on ' + dest_path + ' before you can write to it.'
        sys.exit()

    print '  Removing current playlist...'
    os.popen('find ' + dest_path + ' -iname "*.mp3" -exec rm {} \;')
    os.popen('mkdir -p ' + dest_path)

    print '  Creating file list...'
    file_list = os.popen('find -L "' + src_path + '" -type f -iname "*.mp3"').read().split('\n')[0:-1]

    # loop until there are no more files to copy if the device gets close to full we will stop too
    print '  Starting transfer...\n'
    while (len(file_list) > 0):
        # see how much the player can fit
        free_space = get_free_space(dest_path)
        if (free_space < threshold):
            print '\nAll done!'
            break

        # choose a random file number
        index = random.randint(0, len(file_list) - 1)

        # print information about the file being transferred
        # missing tags are replaced by 'unknown'
        try:
            m = MP3(file_list[index], ID3=EasyID3)
            try:
                print '  ' + m.tags['artist'][0] + ' - ' + m.tags['title'][0]
            except ValueError:
                try:
                    print '  ' + m.tags['artist'][0] + ' - Unknown'
                except ValueError:
                    try:
                        print '  Unknown - ' + m.tags['title'][0]
                    except ValueError:
                        print '  Unknown - Unknown'
            del(m)
        except:
            print '  Problem:', file_list[index]

        # quotes in the file name will F everything up
        file_list[index].replace('"', '\\"')

        # see if it will fit on the player and copy it if so
        if (free_space > get_file_size(file_list[index])):
            os.popen('cp "' + file_list[index] + '" ' + dest_path)

        # Put the last file in our list where the one we just copied was if it's the last file, we'll just toss it
        if (index != len(file_list) - 1):
            file_list[index] = file_list.pop(len(file_list) - 1)
        else:
            file_list.pop(len(file_list) - 1)

if __name__ == '__main__':
    main()
