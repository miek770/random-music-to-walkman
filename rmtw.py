#!/usr/bin/python2

import sys, os, random
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import mutagen.id3
from optparse import OptionParser
from mutagen.mp3 import HeaderNotFoundError

src_path = "/home/michel/Music"
dev_path = "/run/media/michel/SUZIE"
dest_path = dev_path

# When the player only has 5 megs left, we'll stop trying to copy. You
# can lower this to 0 (or anything) so it will try to fit every song in
# your collection, but consider the player might have 2 bytes left and
# you have 800000 songs...
player_is_almost_full = 5000000

#==============================================================================
# Function:    player_is_mounted
# Description: Returns whether or not dev_path is mounted.
#==============================================================================
def player_is_mounted():
    return (os.popen("mount | awk '{print $3}' | grep " + dev_path).read().replace("\n", "") == dev_path)

#==============================================================================
# Function:    get_free_space
# Description: Returns the # of bytes avail on the player.
#==============================================================================
def get_free_space():
    return int(os.popen("df -B 1 | grep `mount | grep " + dev_path + " | awk '{print $1}'`" + " | awk '{print $4}'").read().replace("\n", ""))

#==============================================================================
# Function:    get_file_size
# Description: Returns the # of bytes of a given file name.
#==============================================================================
def get_file_size(file_name):
    return int(os.popen("ls -l \"" + file_name + "\" | awk '{print $5}'").read().replace("\n", ""))

#==============================================================================
# Function:    main
# Description: Main routine. 
#==============================================================================
def main():
    print "Random music to walkman"
    print "  Looking for the mp3 player..."
    if (not player_is_mounted()):
        print "Your mp3 player needs to be mounted on " + dev_path + " before you can write to it."
        sys.exit()

    print "  Removing current playlist..."
    os.popen("find " + dest_path + " -iname '*.mp3' -exec rm {} \;")
    os.popen("mkdir -p " + dest_path)

    print "  Creating file list..."
    file_list = os.popen("find -L \"" + src_path + "\" -type f -iname \"*.mp3\"").read().split("\n")[0:-1]

    # loop until there are no more files to copy if the device gets close to full we will stop too
    print "  Starting transfer...\n"
    while (len(file_list) > 0):
        # see how much the player can fit
        free_space = get_free_space()
        if (free_space < player_is_almost_full):
            print "\nAll done!"
            break

        # choose a random file number
        index = random.randint(0, len(file_list) - 1)

        # print information about the file being transferred
        # missing tags are replaced by 'unknown'
        try:
            m = MP3(file_list[index], ID3=EasyID3)
            try:
                print "  " + m.tags['artist'][0] + " - " + m.tags['title'][0]
            except ValueError:
                try:
                    print "  " + m.tags['artist'][0] + " - Unknown"
                except ValueError:
                    try:
                        print "  Unknown - " + m.tags['title'][0]
                    except ValueError:
                        print "  Unknown - Unknown"
            del(m)
        except:
            print "  Problem:", file_list[index]

        # quotes in the file name will F everything up
        file_list[index].replace("\"", "\\\"")

        # see if it will fit on the player and copy it if so
        if (free_space > get_file_size(file_list[index])):
            os.popen("cp \"" + file_list[index] + "\" " + dest_path)

        # Put the last file in our list where the one we just copied was if it's the last file, we'll just toss it
        if (index != len(file_list) - 1):
            file_list[index] = file_list.pop(len(file_list) - 1)
        else:
            file_list.pop(len(file_list) - 1)

if __name__ == '__main__':
    main()
