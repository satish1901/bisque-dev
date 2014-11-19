from linesman.middleware import *
from linesman.backends.sqlite import SqliteBackend
from linesman.backends.base import Backend
from sqlalchemy import MetaData, Table, Column, ForeignKey
from sqlalchemy.types import DateTime, PickleType, FLOAT, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
import logging
import time
import cPickle
import transaction
from webob import Request, Response

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
    
from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
DeclarativeBase = declarative_base()

log = logging.getLogger("bq.config.middleware.profiler")

class BQProfilingMiddleware(ProfilingMiddleware):
    def __init__(self, app, sqlalchemy_url, profiler_path='__profiler__/', ):
        self.app = app
        self.sqlalchemy_url = sqlalchemy_url
        self.profiler_path = profiler_path
        self.profiling_enabled = True
        self.chart_packages = []
        
        # Attempt to create the GRAPH_DIR
        if not os.path.exists(GRAPH_DIR):
            try:
                os.makedirs(GRAPH_DIR)
            except IOError:
                log.error("Could not create directory `%s'", GRAPH_DIR)
                raise


        # Setup the Mako template lookup
        self.template_lookup = TemplateLookup(directories=[TEMPLATES_DIR])
        
        #self._backend = SqliteBackend()
        self._backend = SqlAlchemyBackend(sqlalchemy_url)
        
        # Set it up
        self._backend.setup()
        log.info('Added profiler')

    def __call__(self, environ, start_response):
        #check if its the profiler ui requested
        req = Request(environ)
        
        wsgi_app = self.app
        if req.path_info_peek() == self.profiler_path.strip('/'):
            req.path_info_pop() #pop __profiler__
            path_info = req.path_info #save path
            path_param = req.path_info_pop() #next reads element
            if not path_param:
                wsgi_app = self.list_profiles(req)
            elif path_param == "graph":
                wsgi_app = self.render_graph(req)
            elif path_param == "media":
                wsgi_app = self.media(req)
            elif path_param == "profiles":
                wsgi_app = self.show_profile(req)
            elif path_param == "delete":
                wsgi_app = self.delete_profile(req)
            elif True:
                # Modify PATH_INFO
                environ['PATH_INFO'] = path_info
                return self.profiler(environ, start_response)
        elif 'HTTP_X_PROFILER' in environ:
            return self.profiler(environ, start_response)
#        else:
#            wsgi_app = HTTPNotFound()
            
        return wsgi_app(environ, start_response)

    
    def profiler(self, environ, start_response):
        _locals = locals()
        prof = Profile()
        start_timestamp = datetime.now()
        prof.runctx("app = self.app(environ, start_response)", globals(), _locals)
        stats = prof.getstats()
        session = ProfilingSession(stats, environ, start_timestamp)
        self._backend.add(session)
        return _locals['app']
            
class Profiler_Sessions(DeclarativeBase):
    __tablename__ = 'profiler'
    uuid      = Column('uuid', String(36), primary_key=True)
    timestamp = Column('timestamp', FLOAT)
    session   = Column('session', PickleType)

#maker = sessionmaker(autoflush=True, autocommit=False,
#                     extension=ZopeTransactionExtension())
#DBSession = scoped_session(maker)

class SqlAlchemyBackend(Backend):
    """
        Opens a connection to a database through SQL Alchemy
    """
    def __init__(self, url='sqlite:///session.db'):
        self.url = url
        self.engine = create_engine(self.url)
        maker = sessionmaker(autoflush=True, autocommit=False)
        self.session = scoped_session(maker)
        self.session.configure(bind=self.engine)
        
    def setup(self):
        """
        Responsible for initializing the backend. for usage.  This is run once
        on middleware startup.
        """
        metadata = DeclarativeBase.metadata
        metadata.create_all(bind=self.engine, checkfirst=True)

    def add(self, session):
        """
        Store a new session in history.
        """
        uuid = session.uuid
        if session.timestamp:
            timestamp = time.mktime(session.timestamp.timetuple())
        else:
            timestamp = None
        log.info('dir %s'%dir(session))
        row = Profiler_Sessions(uuid=uuid, timestamp=timestamp, session=session)
        log.info('adding row %s'%row)
        self.session.add(row)
        self.session.commit()
#        transaction.commit()
        
    def delete(self, session_uuid):
        """
        Removes a specific stored session from the history.
        This should return the number of rows removed (0 or 1).
        """
        count = 0
        for row in self.session.query(Profiler_Sessions).filter(Profiler_Sessions.uuid==session_uuid):
            self.session.delete(row)
            count +=1
        self.session.commit()
        #transaction.commit()
        return count

    def delete_many(self, session_uuids):
        """
        Removes a list of stored sessions from the history.
        This should return the number of rows removed.
        """
        count = 0
        for row in self.session.query(Profiler_Sessions).filter(Profiler_Sessions.uuid.in_(session_uuids)):
            self.session.delete(row)
            count +=1
        self.session.commit()
        #transaction.commit()
        return count
    
    def delete_all(self):
        """
        Removes all stored sessions from the history.
        This should return the number of rows removed.
        """
        count = self.session.Profiler_Sessions.query.delete()
        self.session.commit()
        #transaction.commit()
        return count

    def get(self, session_uuid):
        """
        Returns the data associated with ``session_uuid``.  Should return
        `None` if no session can be found with the specified uuid.
        """
        for row in self.session.query(Profiler_Sessions).filter(Profiler_Sessions.uuid==session_uuid):
            log.info('get %s'%row.session)
            return row.session
        else:
            return None

    def get_all(self):
        """
        Return a dictionary-like object of ALL sessions, where the key is the
        `session uuid`.
        """
        od = OrderedDict()
        for id, session in self.session.query(Profiler_Sessions.uuid, Profiler_Sessions.session).order_by(Profiler_Sessions.timestamp):
            od[id] = session
        log.info('get_all %s'%od)
        return od
    