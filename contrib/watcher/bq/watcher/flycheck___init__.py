
import sys
import time
import logging
import posixpath
import argparse
import subprocess

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, PatternMatchingEventHandler

import bisque_paths

from .which import which


BQPATH="bq-path"

#class  BQEventHamdler(FileSystemEventHandler):
class  BQEventHandler(PatternMatchingEventHandler):
    def __init__(self, prefix, strip, use_link, deletes=False):
        super(BQEventHandler, self).__init__(patterns=None, ignore_patterns=None, ignore_directories=True, case_sensitive=False)
        self.logger = logging.getLogger (__name__)
        self.prefix = prefix
        self.cmd  = "ln" if use_link else "cp"
        self.deletes = deletes
        self.strip  = strip

    def on_created (self, event):
        path = event.src_path
        if path.startswith (self.strip):
            path = path[len(self.strip):]
        path = posixpath.join (self.prefix, path)
        r = subprocess.call ([BQPATH, self.cmd, path])
        self.logger.info ("CREATED %s", path)

    def on_deleted (self, event):
        if self.deletes:
            path = posixpath.join (self.prefix, event.src_path)
            r = subprocess.call ([BQPATH, 'rm', path])
            self.logger.info ("DELETED %s", posixpath.join (self.prefix, event.src_path))


def tri_iter(singleiter):
    iterable = iter(singleiter)
    while True:
        yield next(iterable), next(iterable), next(iterable)

USAGE="""
bq-watcher:  watch a directory and transfer or link files to bisqe

BisQue expects store urls of the form
file://<path>/<file>

Construct a proper store url by providing a
prefix : file://how/your/store/is/configured
dir    : the directory to watch
strip  : left strip this portion from the filenames of the dir to watch

prefix + (file in dir) . replace (^strip, '')
"""
def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    #event_handler = LoggingEventHandler()


    path_cmd = which ("bq-path")
    if path_cmd is None:
        logging.error ("Cannot find bq-path command: use pip install bisque_paths")
        return

    parser = argparse.ArgumentParser(USAGE)
    parser.add_argument("--link", '-l', default=False, action="store_true", help="use linking")
    parser.add_argument("pairs", nargs="*", default=["file:///", ".", "./"], help = "store pairs  file:// dir strip" )
    args = parser.parse_args()
    print args.pairs

    observer = Observer()

    for prefix,path,strip in  tri_iter(args.pairs):
        event_handler = BQEventHandler (prefix, strip=strip, use_link=args.link)
        observer.schedule(event_handler, path, recursive=True)


    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
