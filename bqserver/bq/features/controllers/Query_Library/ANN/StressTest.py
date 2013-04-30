from tables import *
#import pickle
import numpy as np
import scikits.ann 
from scipy.spatial import kdtree
from scipy.spatial import ckdtree
import sys
import time
import ann

import inspect
x=inspect.getmembers(ann)

#sys.setrecursionlimit(10000)
##import os
##treeList = os.listdir('.')
##for treename in treeList:
##    if treename.endswith('.py'):
##        print treename

##path='c:\\bisque\\bqserver\\bq\\features\\controllers\\Query_Library\\ANN\\atree'
#tree = ann.kd_tree('atree',import_kd_tree = True)

#h5file = openFile("descriptors.h5", "r")
#table = h5file.root.Descriptors.GaborTable
##tree = scikits.ann.kdtree(table.cols.value)



# patch module-level attribute to enable pickle to work
#kdtree.node = kdtree.KDTree.node
#kdtree.leafnode = kdtree.KDTree.leafnode
#kdtree.innernode = kdtree.KDTree.innernode

##t0=time.clock()
##t1 = kdtree.KDTree([[1,2,3,4],[2,3,4,5],[3,4,1,2]])
#tree = ann.kd_tree(table.cols.value)
##print 'Calculating Table',time.clock() - t0, "seconds for ann"
##
##t0=time.clock()
##tree.search(np.array([5*np.ones(72)]))
##print 'Querying value', time.clock() - t0, "seconds for ann"

##t0=time.clock()
##t2 = ckdtree.cKDTree(table.cols.value)
##print 'Calculating Table', time.clock() - t0, "seconds for scipy ckdtree"
##
##t0=time.clock()
##t2.query(5*np.ones(72))
##print 'Querying value', time.clock() - t0, "seconds for ann"
##
##t0=time.clock()
##k=scikits.ann.kdtree(table.cols.value)
##print 'Calculating Table', time.clock() - t0, "seconds for scikits"
##
##t0=time.clock()
##k.knn(5*np.ones(72))
##print 'Querying value', time.clock() - t0, "seconds for scikits query"
##
##
##filename='gabortree.txt'
##filehandler = open(filename, 'w')
##pickle.dump(t1, filehandler)
##filehandler.close()
##
##del t1.data
##filename='gabortreesmall.txt'
##filehandler = open(filename, 'w')
##pickle.dump(t1, filehandler)
####filehandler.close()
##
##h5file.close()
