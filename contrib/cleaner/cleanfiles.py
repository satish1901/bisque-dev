#!/usr/bin/python
import os
import sys
import math
import time
import fnmatch
from optparse import OptionParser
import logging
import logging.config

from bq.util.locks import Locks

def iter_files(dirname, include_pattern=None, exclude_pattern=None):
    for dirname, _, filenames in os.walk(dirname):
        for filename in filenames:
            if (include_pattern is not None and not fnmatch.fnmatch(filename, include_pattern)) or \
               (exclude_pattern is not None and fnmatch.fnmatch(filename, exclude_pattern)):
                continue
            fullpath = os.path.join(dirname, filename)
            try:
                (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(fullpath)
                yield (fullpath, atime, size)
            except OSError:
                pass  # skip this file (probably a symbolic link?)

def iter_files_by_atime(dirname, include_pattern=None, exclude_pattern=None):
    return sorted(iter_files(dirname, include_pattern, exclude_pattern), key = lambda tup: (tup[1], -tup[2]))   # sort by increasing atime and decreasing size (delete larger files first)


def main():
    usage="usage %prog [options] directory1 ... directoryn"
    parser = OptionParser(usage)
    parser.add_option('-c','--free', dest="capacity", default='80', help="target free capacity (in percent of drive), default: 80" )
    parser.add_option('-l','--loop', dest="loop", help="wait time between cleaning cycles (in s), default: no cycle" )
    parser.add_option('-r','--dryrun', action="store_true", default=False, help='simulate what would happen')
    parser.add_option('-d','--debug',  action="store_true", default=False, help='print debug log')
    parser.add_option('-i','--include',  dest="include_pattern", default=None, help='filename pattern to include')
    parser.add_option('-e','--exclude',  dest="exclude_pattern", default=None, help='filename pattern to exclude')
    parser.add_option('--log-ini', dest='logini', default=None, help='logging config ini')

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error ("Need at least one directory to clean")
    dirnames = [arg.rstrip('/') for arg in args]

    if options.logini:
        logging.config.fileConfig (options.logini)
    else:
        logging.basicConfig(stream=sys.stdout, level = logging.INFO)

    logger = logging.getLogger ('bq.file_cleaner')

    if options.debug:
        logger.setLevel(logging.DEBUG)

    while True:
        for dirname in dirnames:
            stats = os.statvfs(dirname)
            f_bavail = stats.f_bavail
            f_blocks = stats.f_blocks
            f_bfree = stats.f_bfree
            percent_free = percent_free_last = 100.0 - ((f_blocks-f_bfree) * 100.0 / (f_blocks-f_bfree+f_bavail))
            files_removed = 0
            logger.info("Filesystem %s before cleaning %s%% free" ,  dirname, int(percent_free))
            if percent_free < float(options.capacity):
                for filename, _, size in iter_files_by_atime(dirname, include_pattern=options.include_pattern, exclude_pattern=options.exclude_pattern):
                    try:
                        with Locks(None, filename, failonexist=False, mode='ab') as bq_lock:
                            if bq_lock.locked:
                                # we have exclusive lock => OK to delete
                                if options.dryrun:
                                    logger.info("(simulated) delete %s (%s bytes)" ,  filename, size)
                                    f_bavail += math.ceil(float(size) / float(stats.f_frsize))
                                    f_bfree += math.ceil(float(size) / float(stats.f_frsize))
                                else:
                                    logger.debug("delete %s (%s bytes)" ,  filename, size)
                                    os.remove(filename)
                                    files_removed += 1
                                    if percent_free_last < percent_free-0.1:
                                        # time to refresh stats
                                        stats = os.statvfs(dirname)
                                        f_bavail = stats.f_bavail
                                        f_bfree = stats.f_bfree
                                        percent_free_last = percent_free
                                    else:
                                        f_bavail += math.ceil(float(size) / float(stats.f_frsize))
                                        f_bfree += math.ceil(float(size) / float(stats.f_frsize))
                                percent_free = percent_free_last = 100.0 - ((f_blocks-f_bfree) * 100.0 / (f_blocks-f_bfree+f_bavail))
                                logger.debug("now %s%% free" ,  percent_free)
                            else:
                                logger.info("lock on %s failed, skipping" , filename)
                    except IOError:
                        logger.info("IO error accessing %s, skipping", filename)
                    if percent_free >= float(options.capacity):
                        break
            logger.info("Filesystem %s after cleaning %s%% free, removed %s files" , dirname, int(percent_free), files_removed)

        if options.loop:
            time.sleep(float(options.loop))
        else:
            break

if __name__=="__main__":
    main()
