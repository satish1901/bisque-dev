import os
import subprocess
from threading import Thread
import logging

try: from queue import Queue
except ImportError:
    from Queue import Queue # Python 2.x

logger = logging.getLogger('bq.engine_service.pool')


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        p = os.environ["PATH"].split(os.pathsep)
        p.insert(0, '.')
        for path in p:
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def worker(queue):
    for params in iter(queue.get, None):
        rundir = params['rundir']
        env    = params['env']
        current_dir = os.getcwd()
        command_line = params['command_line']
        os.chdir(rundir)
        if os.name=='nt':
            exe = which(command_line[0])
            exe = exe or which(command_line[0] + '.exe')
            exe = exe or which(command_line[0] + '.bat')
            if exe is None:
                logger.debug('command_line: %s', command_line)
                #raise RunnerException ("Executable was not found: %s" % command_line[0])
                return -1
            command_line[0] = exe
        logger.debug( 'CALLing %s in %s' , command_line,  rundir)
        os.chdir(current_dir)
        try:
            retcode = subprocess.call(command_line,
                                      stdout = open(params['logfile'], 'a'),
                                      stderr = subprocess.STDOUT,
                                      shell  = (os.name == "nt"),
                                      cwd    = rundir,
                                      env    = env,)
            params ['return_code'] =retcode
            callme = 'on_success'
            if retcode != 0:
                callme = 'on_fail'
            callme = params.get(callme)
            if callable(callme):
                callme (params)
        except Exception, e:
            params['with_exception'] = e
            if callable(params.get ('on_fail')):
                params['on_fail'] (params)


class ProcessManager(object):
    "Manage a set of threads to execute limited subprocess"
    def __init__(self, limit=4):
        self.pool = Queue()
        self.threads = [Thread(target=worker, args=(self.pool,)) for _ in range(limit)]
        for t in self.threads: # start workers
            t.daemon = True
            t.start()

    def schedule  (self, process, success=None, fail=None):
        process.setdefault ('on_success', success)
        process.setdefault ('on_fail', fail)
        self.pool.put_nowait (process)

    def stop (self):
        for _ in self.threads: self.pool.put(None) # signal no more commands
        for t in self.threads: t.join()    # wait for completion
