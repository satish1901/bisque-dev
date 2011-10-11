###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

  The Aggregate(Client) Server combines information 
  resources into a single service.  


"""
import logging
from tg import expose
from bq import data_service
from xmlmerge import *
from itertools import chain, islice

log = logging.getLogger('bisque.aggregate')


from bq.core.service import ServiceController


class AggregateService(ServiceController):
    """Aggregate multiple datasource allowing seamless access to
    local and remote dataservers"""
    @expose()
    def index(self, **kw):
        pass


def intialize(uri):
    return AggregateService (uri)



def retrieve(resource_type = None, **kw):
    log.info ('retrieve')
    return ResourceList(data_service.servers(), resource_type, **kw)

def query(resource_type=None, tag_query=None, **kw):
    #results = []
    #docs = [ s.query(resource_type, **kw) for s in data_service.servers() ]
    #merged =  xmlmerge (docs)
    #return merged;
    servers = data_service.servers()
    return ResourceList (servers, resource_type, tag_query=tag_query, **kw)

def count(resource_type, **kw):
    rcount = 0
    servers = data_service.servers()
    for s in servers:   #for every server we know about
        rcount += s.count(resource_type, **kw)  # perform the count on that server
    return rcount

class ResourceList(list):
    def __init__(self, sources, resource_type, tag_query=None, view=None, **kw):
        self.sources = sources
        self.resource_type = resource_type
        self.tag_query = tag_query
        self.view = view
        self.xargs = kw
        rcount = 0
        r = [ (s, None, None) for s in sources ]
#        for s in self.sources:
#                r[s] = (rcount, rcount + s.count(self.resource_type,
#                                                 tag_query=self.tag_query,
#                                                 **self.xargs))
#                rcount = r[s][1]
        self.len = rcount
        self.src_range = r
        log.debug("image_list %s count=%d"% (self.tag_query, self.len))
#        log.debug("image_list sources:" + str (self.sources) )
#        log.debug("image_list range" + str (r) )
    
    def __len__(self):
        log.debug ('aggregate_len %d'% self.len)
        return self.len

    def __getitem__(self, item):
        result = []
        log.debug ("getitem " + str(item))
#        log.debug ("getitem source:" + str(self.sources))
#        log.debug ("getitem range" + str(self.src_range))
        if isinstance(item, slice):
            start = item.start
            stop = item.stop
            s = self.sources[0]
            count = 0
            total_count = 0
            previous_source = None
            for r in self.src_range:
                if previous_source:
                    s = previous_source
                    if s[1] is None:
                        s[1] = s[0].count(self.resource_type,
                                          tag_query = self.tag_query, view=self.view,
                                          **self.xargs)
                    total_count += s[1]
                s = r[0]
                src_result = s.query(self.resource_type,
                                        tag_query = self.tag_query, view=self.view,
                                        offset = max (0, start - total_count),
                                        limit = stop - start -count ,
                                        **self.xargs)
                previous_source = r
                count += len(src_result)
                result += src_result
            return result

            #return islice (chain ( ... ))
            
#             for s in  self.sources:
#                 if r[s][1] < start: continue
#                 result += s.retrieve(self.resource_type,
#                                      tag_query = self.tag_query, view=self.view,
#                                      offset= start - r[s][0],
#                                      limit = min(r[s][1],stop) - start,
#                                      **self.xargs)
#                 start = r[s][1]
#                 if start>=stop: break
#             return result
        else:
            return self[item:item+1][0]
#             for s in  self.sources:
#                 if  not (r[s][0] <= item and item < r[s][1]) : continue
#                 # REPLACE with bisect 
#                 result += s.retrieve(self.resource_type,
#                                      tag_query=self.tag_query, view=self.view,
#                                      offset=item-r[s][0], limit=1,
#                                       **self.xargs)
#             return result[0]
            
    def __getslice__(self, start, end):
        return self.__getitem__(slice(start,end))

            
    def __iter__(self):
        for s in self.sources:
            for n in xrange(s.count(self.resource_type, self.tag_query)):
                yield s.query(self.resource_type,
                                 tag_query=self.tag_query, view=self.view,
                                 offset=n, limit=1,
                                  **self.xargs)
