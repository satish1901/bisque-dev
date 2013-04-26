from tables import *
import ann
import numpy
import re
import random
import os

desc=72 #descriptor length

os.remove('descriptors.h5')

class GaborTable(IsDescription):
    idnumber  = Int64Col()
    uri   = StringCol(2000) 

h5file = openFile("descriptors.h5", mode = "w", title = "Tables of Descriptors")
group = h5file.createGroup("/", 'Descriptors', 'Descriptor Arrays')
Gabortable = h5file.createTable(group, 'GaborTable', GaborTable, "Gabor Descriptors")

descarr = Gabortable.row

lists=['asd','sdf','dfg','fg/h','hjg','wer','tgfde','ed/ws','ytew','edfsd']

for i in range(10):

    descarr['idnumber'] = i
    descarr['uri'] = lists[i]
    descarr.append()

Gabortable.flush()
h5file.close()

h5file=openFile("descriptors.h5",mode = "r", title="Tables of Descriptors")
descarr = h5file.root.Descriptors.GaborTable

uri = 'http://128.111.185.26:8080/image_service/images/62c75e201adc37c3d59de448eee9db0fadfd1546?slice=,,1,1&tile=1,3,0,256&depth=8,f&remap=1,2,3&format=jpeg'
query = 'uri=="%s"'% str(uri)
name = 'uri'

value = [row[name] for row in descarr.where(query)]

h5file.close()

h5file=openFile("descriptors.h5",mode = "a", title="Tables of Descriptors")
GaborTable = h5file.root.Descriptors.GaborTable
descarr = GaborTable.row

descarr['idnumber'] = 12
descarr['uri'] = 'http://128.111.185.26:8080/image_service/images/62c75e201adc37c3d59de448eee9db0fadfd1546?slice=,,1,1&tile=1,3,0,256&depth=8,f&remap=1,2,3&format=jpeg'
descarr.append()
#Gabortable.flush()
h5file.close()


h5file=openFile("descriptors.h5",mode = "r", title="Tables of Descriptors")
descarr = h5file.root.Descriptors.GaborTable

uri = 'http://128.111.185.26:8080/image_service/images/62c75e201adc37c3d59de448eee9db0fadfd1546?slice=,,1,1&tile=1,3,0,256&depth=8,f&remap=1,2,3&format=jpeg'
query = 'uri=="%s"'% str(uri)
name = 'uri'

value = [row[name] for row in descarr.where(query)]

h5file.close()
