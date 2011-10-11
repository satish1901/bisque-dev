#!/usr/bin/python
import os, sys, time
from subprocess import Popen, call
import pkg_resources
import getopt
from urlparse import urlparse

from ConfigParser import SafeConfigParser

PID_TEMPL="bisque_%s.pid" 
LOG_TEMPL='bisque_%s.log'

RUNNER_CMD = ['mexrunner']

SITE_CFG='config/site.cfg'

def readhostconfig ():
    #vars = { 'here' : os.getcwd() }
    config = SafeConfigParser ()
    config.read (SITE_CFG)
    root = config.get ('app:main', 'bisque.root')
    service_hosts = config.items ('servers')

    print "SECTION", config.has_section('servers')

    # Service spec if server.key.url = url
    # Create a dictionary for each host listed
    servers = {}
    for host_spec,val in service_hosts:
        path = host_spec.split('.')

        if not (path[0].startswith('e') or path[0].startswith('h')):
            continue

        param = path[-1]
        d = servers
        for path_el in path[:-1]:
            d = d.setdefault(path_el, {})
        d[param] = val
        #ign, host_id, param = 
        #servers.setdefault(host_id, {})[param] = val
        
    print "ROOT", root, "SERVERS", servers.keys()
    return root, servers


def prepare_log (logfile):
    if os.path.exists(logfile):
        oldlog = logfile + '.save'
        if os.path.exists(oldlog):
            os.remove (oldlog)
        os.rename (logfile, oldlog)
        print ('%s -> %s' % (logfile, oldlog))
    else:
        print ("No logfile %s" % logfile)

# def tail(file):
#     interval = 1.0
#     while True:
#         where = file.tell()
#         line = file.readline()
#         if not line:
#             time.sleep(interval)
#             file.seek(where)
#         else:
#             print line, # already has newline

def tail( f, window=20 ):
    lines= ['']*window
    count= 0
    for l in f:
        lines[count%window]= l
        count += 1
    print lines[count%window:], lines[:count%window]

def check_running (pid_file):
    if os.path.exists(pid_file):
        print "Warning you appear to be restarting another BISQUIK process"
        print "Please stop that process before starting another"
        print "Try to stop previous running instance (Y/n)"
        a = raw_input()
        if a == '' or a[0].upper() == "Y":
            return True
        else:
            return False

if os.name == 'nt':
    import win32api, win32con
    def kill_process(pid):
        try:
            handle = win32api.OpenProcess( win32con.PROCESS_TERMINATE, 0, pid )
            win32api.TerminateProcess( handle, 0 )
            win32api.CloseHandle( handle )
        except:
            print 'Error terminating %s, the process might be dead'%pid
            pass
        #import subprocess
        #subprocess.call(['taskkill', '/PID', str(pid), '/F'])

else:        
    import signal
    def kill_process(pid):
        print "killing %d " % pid
        try:
            pid = os.getpgid(pid)
            os.killpg (pid, signal.SIGTERM)
        except OSError, e:
            print "kill process %s failed with %s"  % (pid, e)
            

def operation(command, options, *args):
    #pkg_resources.require('BisqueCore >=0.4')
    if not os.path.exists(SITE_CFG):
        print "Cannot find site.cfg.. please make sure you are in the bisque dir"
        return

    try:
        root, servers = readhostconfig()
        for key, serverspec in sorted(servers.items()):
            print key, serverspec

            url = serverspec.pop('url')
            fullurl = urlparse (url)
            services_enabled = ','.join([
                l.strip() for l in serverspec.pop('services_enabled','').split(',')])
            services_disabled = ','.join([
                l.strip() for l in serverspec.pop('services_disabled','').split(',')])

            host = fullurl[1].split(':')[0]
            port = str(fullurl.port)

            proxyroot = serverspec.pop('proxyroot', '')

            logfile = LOG_TEMPL % port
            pidfile = PID_TEMPL % port

            if command in ('start') and check_running(pidfile):
                call ([sys.argv[0], 'servers', 'stop'])

            if command in ('start', 'restart'):
                prepare_log (logfile)

            msg = { 'start': 'starting', 'stop':'stopping', 'restart':'restarting'}[command]
            print ("%s bisque on %s .. please wait" %  (msg, port) )
            server_cmd = ['paster', 'serve']
            server_cmd.extend ([
                          '--log-file', logfile,
                          '--pid-file', pidfile,
                          #                   '--deamon',
                          ])
            if options.reload:
                server_cmd.append ('--reload')
            server_cmd.extend ([
                          'config/server.ini',
                          command,
                          'services_enabled=%s' % services_enabled,
                          'services_disabled=%s' % services_disabled,
                          'http_port=%s' % port,
                          'http_host=%s' % host,
                          'rooturl=%s' % root,
                          'proxyroot=%s' % proxyroot,
                          ])
            # server_cmd.extend ([ "%s=%s" % (k,v) for k,v in serverspec.items()])

            server_cmd.extend (args)


            if options.verbose:
                print 'Executing: %s' % ' '.join(server_cmd)
                
            if not options.dryrun:
                pid_root =Popen(server_cmd).pid

        if options.verbose:
            print '%s: %s' % (command , ' '.join(RUNNER_CMD))

        if command == 'start':
            if not options.dryrun:
                logfile = open('mexrunner.log', 'wb')
                mexrunner_pid = Popen(RUNNER_CMD, stdout = logfile, stderr = logfile ).pid
                open('mexrunner.pid', 'wb').write(str( mexrunner_pid ))
            print "Starting Mexrunner: %s"%mexrunner_pid
        else:
            import signal
            if os.path.exists('mexrunner.pid'):
                if not options.dryrun:
                    f = open('mexrunner.pid', 'rb') 
                    mexrunner_pid = int(f.read())
                    f.close()
                    kill_process(mexrunner_pid)
                    os.remove ('mexrunner.pid')
                print "Stopped Mexrunner: %s"%mexrunner_pid
                

            #if command in ('start', 'restart'):
            #    time.sleep(5)
            #if command in ('start', 'restart'):
            #    LOG = open (logfile, 'rU')
            #    tail (LOG)
    except KeyboardInterrupt:
        pass
    except:
        raise



