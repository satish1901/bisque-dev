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
    """Worker waits forever command requests and executes one command at a time

    @param queue: is a queue of command requests

    requests  = {
      command_line : ['processs', 'arg1', 'arg1']
      rundir       : 'directory to run in ',
      logfile      :  'file to  write stderr and stdout',
      on_success   : callback with (request) when success,
      on_fail      : callback with (request) when fail,
      env          : dict of environment
    }

    This routine will add the following fields:
    {
       return_code : return code of the command
       with_exception : an exception when exited with excepttion
    }
    """
    for request in iter(queue.get, None):
        rundir = request['rundir']
        env    = request['env']
        callme = request.get ('on_fail') # Default to fail
        request.setdefault('return_code',1)

        current_dir = os.getcwd()
        command_line = request['command_line']
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
                                      stdout = open(request['logfile'], 'a'),
                                      stderr = subprocess.STDOUT,
                                      shell  = (os.name == "nt"),
                                      cwd    = rundir,
                                      env    = env,)
            request ['return_code'] =retcode
            if retcode == 0:
                callme = request.get('on_success')
        except Exception, e:
            request['with_exception'] = e
        finally:
            if callable(callme):
                callme(request)




class ProcessManager(object):
    "Manage a set of threads to execute limited subprocess"
    def __init__(self, limit=4):
        self.pool = Queue()
        self.threads = [Thread(target=worker, args=(self.pool,)) for _ in range(limit)]
        for t in self.threads: # start workers
            t.daemon = True
            t.start()

    def schedule  (self, process, success=None, fail=None):
        """Schedule  a process to be run when a worker thread is available

        @param process: a request see "worker"
        @param success:  a callable to call on success
        @param fail:  a callable to call on failure
        """
        process.setdefault ('on_success', success)
        process.setdefault ('on_fail', fail)
        self.pool.put_nowait (process)

    def stop (self):
        for _ in self.threads: self.pool.put(None) # signal no more commands
        for t in self.threads: t.join()    # wait for completion
