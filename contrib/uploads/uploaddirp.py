#!/usr/bin/env python

import os
import sys
import bqapi
import multiprocessing

def sendimage_to_bisque(root, user, passwd, image_path, meta_path=None):
    "Send one image to bisque"
    session = bqapi.BQSession ().init_local(user, passwd, bisque_root=root, create_mex=False)
    if meta_path:
         meta_path = open (meta_path).read()
    session.postblob (image_path, xml = meta_path)
    session.close()

def sendimage_helper (arg_tuple):
    "Expand tuple args"
    sendimage_to_bisque (*arg_tuple)

root = 'https://loup.ece.ucsb.edu/'
user='kgk'
passwd = 'testme'

def main(argv):
    direct = argv[1]
    if not os.path.isdir (direct):
        print "Usage uploaddirp <directory>"
        sys.exit (1)

    pool = multiprocessing.Pool(6)
    files = os.listdir (direct)
    print "Uploading ", files
    pool.map (sendimage_helper, [ (root, user, passwd, f) for f in os.listdir (direct) ])



if __name__ == "__main__":
    main(sys.argv)
