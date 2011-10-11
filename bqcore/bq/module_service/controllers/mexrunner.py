from __future__ import with_statement

import time
import socket
import threading
import Queue
import logging
import transaction

import tg
from tg import config, url
from lxml import etree
from datetime import datetime, timedelta
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import scoped_session, sessionmaker, mapper as sa_mapper

import bq
#from bq import data_service
from bq.core.model import  DBSession 
from bq.data_service.model import ModuleExecution as Mex, Service, Module
from bq.util import http
from bq.util.bisquik2db import bisquik2db, load_uri, db2tree, updateDB
from bq.core.identity import set_admin_mode

QWAIT = config.get ('bisque.module_service.queue_wait', 20)


def index(seq, f):
    """Return the index of the first item in seq where f(item) == True."""
    for index in (i for i in xrange(len(seq)) if f(seq[i])):
        return index
# Python 2.6
#def index(seq, f):
#    """Return the index of the first item in seq where f(item) == True."""
#    return next((i for i in xrange(len(seq)) if f(seq[i])), None)
    
log = logging.getLogger('bq.module_service.mexrunner')



#Session = sessionmaker(autoflush=True, autocommit=False, extension=ZopeTransactionExtension())
#Session = sessionmaker(autoflush=True, autocommit=False)
#Session = scoped_session(Session)

def load_db(dbtype, url, session = DBSession):
    db_id = url.rsplit('/', 1)[1]
    return  session.query(dbtype).get(db_id)
     


class MexRequest(object):
    "container for mex request"
    def __init__(self, mex, service, baseuri):
        self.mex = mex
        self.service  = service
        self.reload()

        self.mexuri = "%s%s" % (baseuri,  mex.uri)
        self.mextree = db2tree(mex, view='deep', baseuri = baseuri)
        #module_xml = data_service.load(mex.module, view='deep')
        #log.debug ("module %s -> %s" % (mex.module, module_xml))
        #self.modtree = etree.XML(module_xml)
        module = load_db(Module, mex.module)
        self.modtree = db2tree(module, view='deep', baseuri=baseuri)
        log.debug ("MODULE = %s"  % etree.tostring (self.modtree))
        self.mex_id = mex.uri.rsplit('/', 1)[1]
        # End the transaction so the http request is
        # not part of it.
        self.asynch = self.modtree.xpath('//tag[@name="asynchronous"]')
        self.service_uri = service.engine

    def reload(self):
        self.mex = DBSession.merge(self.mex)
        self.service = DBSession.merge(self.service)
        


class MexResponse(object):
    "container for mex response"
    def __init__(self, request, resp, content):
        self.request = request
        self.resp = resp
        self.body = content
        self.status = int (resp['status'].split()[0])
        self.reason =  getattr(resp, 'reason', 'Unavailable')


    
#class MexRunner (threading.Thread):
class MexRunner(object):
    runner_count = 0

    def __init__(self, baseuri):
        #threading.Thread.__init__(self, name="mexrunner")
        #self.requests = Queue.Queue()
        #self.setDaemon(True)
        #self.timeout = int(QWAIT)# Check for restored servers every so often
        self.baseuri = baseuri
        #self.submit (None)

        #sqlengine = tg.config['pylons.app_globals'].sa_engine
        #Session.configure(bind=sqlengine)
        self.__class__.runner_count = self.__class__.runner_count +1

        



    def find_active_service(self, mex):
        engine = None
        log.info ('service for mex = %s and module %s' % (mex.uri, mex.module))
        engines = self.session.query(Service).filter_by(
            module = mex.module).all()
        # Choose an (enabled) engine
        for engine in list(engines):
            engine_status = engine.findtag('status')
            if engine_status and engine_status.value == 'disabled':
                engines.remove (engine)
        log.info ('service for mex=%s/module %s=%s'
                  % (mex.uri, mex.module, engines))
        return engines


    def prepare_request(self, mex, service, baseuri):
        mex = DBSession.merge(mex)
        mex.status = 'DISPATCH'
        return MexRequest(mex, service, baseuri)

        
    def dispatch_mex(self, request):
        log.debug ("DISPATH FOR: %s is asynch: %s"
                   % ( request.modtree.get('name'), request.asynch))
            
        body = etree.tostring(request.mextree)

        service_uri = request.service_uri
        log.info("DISPATCH: POST %s (%s) with %s"
                 % (service_uri, request.mexuri, body))
        try: 
            resp, content = http.xmlrequest(service_uri +"/execute", "POST", 
                                            body = body,
                                            headers = {'Mex': request.mex_id})
        except socket.error:
            resp = {'status':'503'}
            content = ""
        log.debug ("DISPATCH: RESULT %s->%s %s"
                   % (service_uri, resp['status'], content))
        response =  MexResponse(request, resp, content)
        #self._post_dispatch(response)
        return response


    def _post_dispatch(self, response):
        """manage the response of the dispatch

        return whether dispatch success 
        """
        if response.status != 200:
            # Depending on return code, we will update the engine/service
            # availability i.e. after a bunch of tries disable the service
            # and notify the admin
            log.info ("DISPATCH to %s FAILED" % response.request.service.engine)
            return False
        return True



    def process_response(self, response):
        """Clean up the mex after an attempted dispatch
        """
        # Check the post succedded
        if response.status != 200:
            # Depending on return code, we will update the engine/service
            # availability i.e. after a bunch of tries disable the service
            # and notify the admin
            log.info ("DISPATCH to %s FAILED" % response.request.service.engine)
        if response.status == 200:
            # We received a good status so we update the last-contact
            contact = response.request.service.findtag('last-contact')
            contact.value = str(datetime.now())
            # End this this request if non-asynchronous
            if not response.request.asynch:
                mex = self.end_response(response)
            else:
                log.debug("ASYNCH: DISPATCH")
                mex = response.request.mex

        else: #  resp['status'] != "200":
            mex = self.end_response(response)
        log.debug ("END DISPATCH")
        return mex


    def end_response(self, response):
        """Try to parse the response content and determine if
        we recieved a valid Mex.  If so use the contents
        """
        mex = response.request.mex
        mexuri = response.request.mexuri
        self.session.refresh(mex)

        content = response.body
        try:
            if response.status in ( 200, 500):
                mextree = etree.XML(content)
                if  mextree.tag == 'response':
                    mextree = mextree[0]
            else:
                mextree = response.request.mextree
        except etree.ParseError:
            mextree = etree.Element ('mex', status='FAILED')
            log.warn("Bad Mex Content %s" % content)

        if mextree.get ('uri', None) != mexuri:
            log.error ("wrong mex returned %s" % mextree.get ('uri'))
            mextree.set('uri', mexuri)

        etree.SubElement(mextree, 'tag',
                         name="end-time",
                         value=time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime()))
        if  mextree.get('status') not in ['FINISHED', 'FAILED' ]:
            mextree.set('status', 'FAILED')
            
        if response.status != 200:
            etree.SubElement (mextree, 'tag',
                              name="http-status",
                              value=str(response.status))
            
            etree.SubElement (mextree, 'tag',
                              name="http-error",
                              value=response.reason)

        log.info ("MEX SAVE")
        bisquik2db(mextree)
        #self.session.refresh (mex)

        log.info ('END_MEX %s->%s' % (mex.uri, mex.status))
            
        return mex



    def process_one(self, mex, service):
        with transaction.manager:
            request = self.prepare_request(mex, service, self.baseuri)
        #self.session.flush()

        response = self.dispatch_mex(request)

        with transaction.manager:
            response.request.reload()
            self.process_response(response)
        #self.session.flush()
        return request, response


    def process_pending(self, mex_id=None):
        """return the list of dispatchable mexes"""
        print "PROCESSING"
        log.info('processing')
        if self.runner_count > 1:
            log.error ("RUNNER COUNT")

        self.session = DBSession
        self.session.autoflush = False
        # Create service pairs 
        pending = self.session.query(Mex).filter_by(status='PENDING')
        for mex in pending:
            for service in  self.find_active_service (mex):
                request, response = self.process_one(mex, service)
                if response.status == 200:
                    break
        self.session.remove()
        


    def run(self):
        log.info ("STARTING %s" % id(self))
        set_admin_mode(True)
        mex_id = None
        while True:
            log.debug ("WAIT REQUEST %s" % self.timeout)
            try:
                mex_id = self.requests.get(True, self.timeout)
                log.debug ("GOT REQUEST %s" % mex_id)
            except Queue.Empty, e:
                log.debug ("TIMEOUT")
                mex_id = None
            self.process_pending(mex_id)
        
    def submit (self, mex_id):
        self.requests.put (mex_id)

    def __str__(self):
        """Dump the status of the runner """
        


