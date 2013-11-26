import os
import time

if os.name == 'nt':
    def walltime():
        return time.clock()
else:
    def walltime():
        return time.time()


class Timer(object):#pylint disable-msg=R0903
    """
    Time a set of statement or a function
    with Timer() as t:
      somefun()
      somemorefun()
    log.info ("fun took %.03f seconds" % t.interval)

    """
    def __enter__(self):
        self.start = walltime()
        return self
    def __exit__(self, *args):
        self.end = walltime()
        self.interval = self.end - self.start


