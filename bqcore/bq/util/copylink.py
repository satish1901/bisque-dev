import os,sys
import shutil
import logging

log = logging.getLogger('bq.util.copylink')

def copy_link (*largs):
    largs = list (largs)
    d = largs.pop()
        
    for f in largs:
        if not os.path.exists(f):
            log.warn("can't copy %s" %f)
            continue
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            log.info ("linking %s to %s"%(f,dest))
            if os.path.exists(dest):
                log.info ("Found existing file %s: removing .." % dest)
                os.unlink (dest)
            os.link(f, dest)
        except (OSError, AttributeError), e:
            log.info ("Problem in link %s .. trying copy" % e)
            if os.path.isdir(f):
                shutil.copytree(f, dest)
            else:
                shutil.copy2(f, dest)
        
                              
