#!/usr/bin/python
import os
import sys
import math
import time
from optparse import OptionParser
import logging

from bq.util.locks import Locks


logging.basicConfig(stream=sys.stdout, level = logging.INFO)



def iter_files(dirname):
    for dirname, _, filenames in os.walk(dirname):
        for filename in filenames:
            fullpath = os.path.join(dirname, filename)
            try:
                (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(fullpath)
                yield (fullpath, atime, size)
            except OSError:
                pass  # skip this file (probably a symbolic link?)
            
def iter_files_by_atime(dirname):
    return sorted(iter_files(dirname), key = lambda tup: (tup[1], -tup[2]))   # sort by increasing atime and decreasing size (delete larger files first)


def main():
    usage="usage %prog [options] directory1 ... directoryn"
    parser = OptionParser(usage)
    parser.add_option('-c','--capacity', dest="capacity", default='80', help="target free capacity (in percent of drive), default: 80" )
    parser.add_option('-l','--loop', dest="loop", help="wait time between cleaning cycles (in s), default: no cycle" )
    parser.add_option('-r','--dryrun', action="store_true", default=False, help='simulate what would happen')
    parser.add_option('-d','--debug',  action="store_true", default=False, help='print debug log')

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error ("Need at least one directory to clean")
    dirnames = [arg.rstrip('/') for arg in args]
    
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    while True:
        for dirname in dirnames:
            stats = os.statvfs(dirname)
            f_bavail = stats.f_bavail
            f_blocks = stats.f_blocks
            percent_free = percent_free_last = f_bavail * 100.0 / f_blocks
            logging.info("Filesystem %s before cleaning %s%% free" % (dirname, int(percent_free)))
            if percent_free < float(options.capacity):    
                for filename, _, size in iter_files_by_atime(dirname):
                    with Locks(None, filename, failonexist=False, mode='ab') as bq_lock:
                        if bq_lock.locked:
                            # we have exclusive lock => OK to delete
                            if options.dryrun:
                                logging.debug("(simulated) delete %s (%s bytes)" % (filename, size))
                                f_bavail += math.ceil(float(size) / float(stats.f_frsize))
                            else:
                                logging.debug("delete %s (%s bytes)" % (filename, size))
                                os.remove(filename)
                                if percent_free_last < percent_free-0.1:
                                    # time to refresh stats
                                    stats = os.statvfs(dirname)
                                    f_bavail = stats.f_bavail
                                    percent_free_last = percent_free
                                else:
                                    f_bavail += math.ceil(float(size) / float(stats.f_frsize))
                            percent_free = f_bavail * 100.0 / f_blocks
                            logging.debug("now %s%% free" % percent_free)
                        else:
                            logging.debug("lock on %s failed, skipping" % filename)
                    if percent_free >= float(options.capacity):
                        break
            logging.info("Filesystem %s after cleaning %s%% free" % (dirname, int(percent_free)))
            
        if options.loop:
            time.sleep(float(options.loop))
        else:
            break

if __name__=="__main__":
    main()
    