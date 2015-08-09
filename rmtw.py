#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys, os, random, shutil, re
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import mutagen.id3
from optparse import OptionParser
from mutagen.mp3 import HeaderNotFoundError

#==============================================================================
# Function:    clean(string)
# Description: Returns the string free of trailing whitespaces an non-ascii
#              characters (the latter are replaced by underscores).
#==============================================================================
def clean(string):
    return re.sub('[^\w\-_\. ]', '_', string).rstrip()

#==============================================================================
# Function:    touch(fname, times=None)
# Description: Updates a file or directory's access and modification times
#              (atime and mtime). Sadly ctime can't be modified as easily.
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
# Class:       Player 
# Description: MP3 player (or USB key)
#==============================================================================
class Player:

    # Initialization
    #================
    def __init__(self, src_path, dest_path, threshold):
        self.src_path = src_path
        self.dest_path = dest_path
        self.threshold = threshold
        self.total_size = self.get_free_space()
        self.free_space = self.total_size

        self.file_list = None
        self.final_list = list()

        print 'Random music to walkman'
        print '  Looking for the mp3 player...'
        if (not self.is_mounted()):
            print 'Your mp3 player needs to be mounted on ' + self.dest_path + ' before you can write to it.'
            sys.exit()

    # Generate mp3 list from source path
    #====================================
    def get_mp3_list(self):
        l = list()
        for root, dirs, files in os.walk(self.src_path):
            for f in files:
                if f.endswith(".mp3"):
                    l.append(os.path.join(root, f))
        return l

    # Returns the # of bytes available on the player
    #================================================
    def get_free_space(self):
        return int(os.popen("df -B 1 | grep {} | awk '{{print $4}}'".format(self.dest_path)).read().replace("\n", ""))

    # Fill the player
    #=================
    def fill(self):
        print '  Removing current playlist...'
        self.clear_directory()
        self.total_size = self.get_free_space()
        self.free_space = self.total_size

        print '  Creating file list...'
        self.file_list = self.get_mp3_list()

        # loop until there are no more files to copy if the device gets close to full we will stop too
        while (len(self.file_list) > 0):

            # see how much the player can fit
            if (self.free_space < self.threshold):
                break

            # choose a random file number
            index = random.randint(0, len(self.file_list) - 1)

            try:
                m = MP3(self.file_list[index], ID3=EasyID3)

                # Only copy the song if the artist and title tags are set
                if not 'artist' in m.tags.keys():
                    raise ValueError('artist tag missing')

                if not 'title' in m.tags.keys():
                    raise ValueError('title tag missing')

                # see if it will fit on the player and copy it if so
                fsize = os.path.getsize(self.file_list[index])
                if (self.free_space > fsize):
                    self.final_list.append((m.tags['artist'][0], m.tags['title'][0], self.file_list[index], fsize))
                    self.free_space -= fsize

            except AttributeError, e:
                print "! AttributeError: {} - {}".format(e, self.file_list[index])

            except ValueError, e:
                print "! ValueError: {} - {}".format(e, self.file_list[index])

            except KeyError, e:
                print "! KeyError: {} - {}".format(e, self.file_list[index])

            except TypeError, e:
                print "! TypeError: {} - {}".format(e, self.file_list[index])

            del(m)

            # Put the last file in our list where the one we just copied was if it's the last file, we'll just toss it
            # Not really sure anymore what's the point of this function. Might be removed in the near future...
            if (index != len(self.file_list) - 1):
                self.file_list[index] = self.file_list.pop(len(self.file_list) - 1)
            else:
                self.file_list.pop(len(self.file_list) - 1)

        self.sync()

    # Sorts the final songs list and syncs them to the player
    #=========================================================
    def sync(self):
        if len(self.final_list):
            print "\n  Syncing to player..."
            self.final_list.sort()
            synced = 0

            for i in self.final_list:

                sys.stdout.write("\r%d%%" % int(100*synced/self.total_size))
                sys.stdout.flush()

                # Create artist folder if it doesn't exist
                artist_dir = os.path.join(self.dest_path, clean(i[0]))
                if not os.path.exists(artist_dir):
                    os.mkdir(artist_dir)

                shutil.copyfile(i[2], artist_dir + "/{}.mp3".format(clean(i[1])))

                synced += i[3]

        else:
            print "No file list to sync, nothing to do."

    # Returns whether or not the player is mounted
    #==============================================
    def is_mounted(self):
        return (os.popen("mount | awk '{print $3}' | grep " + self.dest_path).read().replace("\n", "") == self.dest_path)

    # Erases all subdirectories on the player
    #=========================================
    def clear_directory(self):
        for the_file in os.listdir(self.dest_path):
            file_path = os.path.join(self.dest_path, the_file)

            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

            except Exception, e:
                print e

#==============================================================================
# Function:    main()
# Description: Main routine. 
#==============================================================================
def main():
    # Options and arguments definition
    usage = 'usage: %prog [OPTION]... [SOURCE] [DEST]'
    parser = OptionParser(usage=usage)
    parser.add_option('-t',
                      '--threshold',
                      default=5000000,
                      action='store',
                      help='Set the size threshold in byte at which the script stops copying (default=5000000)')

    # Arguments handling
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit()

    p = Player(src_path=os.path.join(args[0]),
               dest_path=os.path.join(args[1]),
               threshold=options.threshold)

    p.fill()

if __name__ == '__main__':
    main()
