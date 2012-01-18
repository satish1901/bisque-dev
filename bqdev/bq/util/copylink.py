
import os,sys
import shutil

def copy_link (*largs):
    largs = list (largs)
    d = largs.pop()
        
    for f in largs:
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            print ("linking %s to %s"%(f,dest))
            if os.path.exists(dest):
                print ("Found existing file %s: removing .." % dest)
                os.unlink (dest)
            os.link(f, dest)
        except (OSError, AttributeError), e:
            print ("Problem in link %s .. trying copy" % e)
            if os.path.isdir(f):
                shutil.copytree(f, dest)
            else:
                shutil.copy2(f, dest)
        
                              
