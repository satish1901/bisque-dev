# locks.py
# Authors: Kris Kvilekval and Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara

""" Functions to call BioImageConvert command line tools.
"""

__module__    = "locks"
__author__    = "Kris Kvilekval and Dmitry Fedorov"
__version__   = "1.1"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"


import os
import time
import logging
import threading

from read_write_locks import HashedReadWriteLock
import  XFile


rw = HashedReadWriteLock()
LOCK_SLEEP = 0.3
MAX_SLEEP  = 8

class Locks (object):
    log = logging.getLogger('bq.image_service.locks')

    def debug(self, msg):
        """Log detailed info about the locking of threads and files"""
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug ("LOCKING: %s (%s,%s): %s" %
                            (threading.currentThread().getName(),
                             self.ifnm, self.ofnm, msg))


    def __init__(self, ifnm, ofnm=None, failonexist=False, mode="wb"):
        self.wf = self.rf = None
        self.ifnm = ifnm
        self.ofnm = ofnm
        self.mode = mode
        self.locked = False
        self.thread_r = self.thread_w = False
        self.failonexist = failonexist

    def acquire (self, ifnm=None, ofnm=None):

        self.debug ("acquire0 thread-r")
        if ifnm:
            rw.acquire_read(ifnm)
            self.thread_r = True

        self.debug ("acquired thread-r")

        if ifnm and os.name != "nt":
            self.debug ("->RL")
            lock_sleep=LOCK_SLEEP
            while True:
                try:
                    self.rf = XFile.XFile(ifnm, 'rb')
                    self.rf.lock(XFile.LOCK_SH|XFile.LOCK_NB)
                    self.debug ("GOT RL")
                    break
                except XFile.LockError:
                    self.debug ("RL sleep %s" % lock_sleep)
                    time.sleep(lock_sleep)
                    lock_sleep *= 2
                    if lock_sleep > MAX_SLEEP:
                        lock_sleep = MAX_SLEEP


        if ofnm:
            self.debug ("acquire0 thread-w")
            rw.acquire_write(ofnm)
            self.thread_w = True
            if self.failonexist and os.path.exists (ofnm):
                self.debug ("out file exists: bailing")
                self.release()
                return

        if ofnm and os.name != "nt":
            self.debug ("->WL")
            #open (ofnm, 'w').close()
            self.wf = XFile.XFile(ofnm, self.mode)
            try:
                self.wf.lock(XFile.LOCK_EX|XFile.LOCK_NB)
                self.debug ("GOT WL")
            except XFile.LockError:
                self.debug ("WL failed")
                self.wf.close()
                self.wf = None
                self.release()
                return


        self.locked = True


    def release(self):
        if self.wf:
            self.debug ("RELEASE WF")
            self.wf.unlock()
            self.wf.close()
            try:
                stats = os.stat (self.wf.name)
                if stats.st_size == 0:
                    self.debug ('release: unlink 0 length file %s' % stats)
                    os.unlink (self.wf.name)
            except OSError:
                pass
            self.wf = None

        if self.ofnm and self.thread_w:
            self.debug ("release thread-w")
            rw.release_write(self.ofnm)
            self.thread_w = False

        if self.rf:
            self.debug ("RELEASE RF")
            self.rf.unlock()
            self.rf.close()
            self.rf = None

        if self.ifnm and self.thread_r:
            self.debug ("release thread-r")
            rw.release_read(self.ifnm)
            self.thread_r = False

        self.locked = False

    def __enter__(self):
        self.acquire(self.ifnm, self.ofnm)
        return self
    def __exit__(self, type, value, traceback):
        self.release()

