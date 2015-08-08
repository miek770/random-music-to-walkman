#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys, os, random, shutil, re
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import mutagen.id3
from optparse import OptionParser
from mutagen.mp3 import HeaderNotFoundError

#==============================================================================
# Function:    
# Description: 
#==============================================================================
def clear_directory(path):
    for the_file in os.listdir(path):
        file_path = os.path.join(path, the_file)

        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        except Exception, e:
            print e

#==============================================================================
# Function:    
# Description: 
#==============================================================================
def clean(string):
    return re.sub('[^\w\-_\. ]', '_', string)

#==============================================================================
# Function:    
# Description: 
#==============================================================================
def touch(fname, times=None):

    # Assume fname is a file
    try:
        with open(fname, 'a'):
            os.utime(fname, times)

    # fname is a directory, not a file
    except IOError:
        os.utime(fname, times)

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
    clear_directory(dest_path)

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

        try:

            # print information about the file being transferred
            # missing tags are replaced by 'unknown'
            m = MP3(file_list[index], ID3=EasyID3)

            # Only copy the song if the artist and title tags are set
            print '  ' + m.tags['artist'][0] + ' - ' + m.tags['title'][0]

            # Create artist folder if it doesn't exist
            artist_dir = os.path.join(dest_path, clean(m.tags['artist'][0]))
            if not os.path.exists(artist_dir):
                os.mkdir(artist_dir)

            # see if it will fit on the player and copy it if so
            if (free_space > os.path.getsize(file_list[index])):
                shutil.copyfile(file_list[index], artist_dir + "/{}.mp3".format(clean(m.tags["title"][0])))

        except ValueError, e:
            print "! ValueError: {} - {}".format(e, file_list[index])

        except KeyError, e:
            print "! KeyError: {} - {}".format(e, file_list[index])

        except TypeError, e:
            print "! TypeError: {} - {}".format(e, file_list[index])

        del(m)

        # Put the last file in our list where the one we just copied was if it's the last file, we'll just toss it
        if (index != len(file_list) - 1):
            file_list[index] = file_list.pop(len(file_list) - 1)
        else:
            file_list.pop(len(file_list) - 1)

    # Lastly, touch each folder in alphabetical order to correct my stupid MP3 player sorting order
    l = os.listdir(dest_path)
    l.sort()
    for d in l:
        touch(os.path.join(dest_path, d)

if __name__ == '__main__':
    main()
