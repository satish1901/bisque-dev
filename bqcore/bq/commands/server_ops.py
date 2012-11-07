#!/usr/bin/python
import os, sys, time
from subprocess import Popen, call
import pkg_resources
import getopt
from urlparse import urlparse
from ConfigParser import SafeConfigParser

from bq.util.commands import asbool, find_site_cfg

#from bq.commands.server_ops import root

PID_TEMPL = "bisque_%s.pid" 
LOG_TEMPL = 'bisque_%s.log'

RUNNER_CMD = ['mexrunner']

SITE_CFG = 'site.cfg'
UWSGI_ENGINE_CFG = 'uwsgi_engine.cfg.default'
UWSGI_CLIENT_CFG = 'uwsgi_client.cfg.default'

if os.name == 'nt':
    import win32api, win32con
    def kill_process(pid):
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
            win32api.TerminateProcess(handle, 0)
            win32api.CloseHandle(handle)
        except:
            print 'Error terminating %s, the process might be dead' % pid
            pass
        #import subprocess
        #subprocess.call(['taskkill', '/PID', str(pid), '/F'])

else:        
    import signal
    def kill_process(pid):
        try:
            pid = os.getpgid(pid)
            os.killpg (pid, signal.SIGTERM)
        except OSError, e:
            print "kill process %s failed with %s" % (pid, e)
            

#####################################################################
# utils


def readhostconfig (site_cfg):
    #vars = { 'here' : os.getcwd() }
    config = SafeConfigParser ()
    config.read (site_cfg)
    root = config.get ('app:main', 'bisque.root')
    service_items = config.items ('servers')
    hosts = [ x.strip() for x in config.get  ('servers', 'servers').split(',') ] 

    #print "SECTION", config.has_section('servers')

    # Service spec if server.key.url = url
    # Create a dictionary for each host listed
    servers = {}
    for host_spec, val in service_items:
        path = host_spec.split('.')

        #if not (path[0].startswith('e') or path[0].startswith('h')):
        if not path[0] in hosts:
            continue

        param = path[-1]
        d = servers
        for path_el in path[:-1]:
            d = d.setdefault(path_el, {})
        d[param] = val
        #ign, host_id, param = 
        #servers.setdefault(host_id, {})[param] = val


    bisque = { 'root': root, 'servers': servers, 'log_dir': '.', 'pid_dir' : '.' }
    if config.has_option('servers', 'log_dir'):
        bisque['log_dir'] = config.get ('servers', 'log_dir')
    if config.has_option('servers', 'pid_dir'):
        bisque['pid_dir'] = config.get ('servers', 'pid_dir')
    if config.has_option('servers','backend'):
        bisque['backend'] = config.get ('servers', 'backend')
    if config.has_option('servers','mex_dispatcher'):
        bisque['mex_dispatcher'] = config.get ('servers', 'mex_dispatcher')
    return bisque


def prepare_log (logfile):
    if os.path.exists(logfile):
        oldlog = logfile + '.save'
        if os.path.exists(oldlog):
            os.remove (oldlog)
        os.rename (logfile, oldlog)
        #print ('%s -> %s' % (logfile, oldlog))
    #else:
    #    print ("No logfile %s" % logfile)

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

def tail(f, window=20):
    lines = [''] * window
    count = 0
    for l in f:
        lines[count % window] = l
        count += 1
    print lines[count % window:], lines[:count % window]

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
        
def paster_command(command, options, cfgopt, processes, args):
    def verbose(msg):
        if options.verbose:
            print msg
        
    paster_verbose = '-v' if options.verbose else '-q'
    msg = { 'start': 'starting', 'stop':'stopping', 'restart':'restarting'}[command]
    verbose ("%s bisque on %s .. please wait" % (msg, cfgopt['port']))
    server_cmd = ['paster', 'serve', paster_verbose]
    server_cmd.extend (['--log-file', cfgopt['logfile'], '--pid-file', cfgopt['pidfile'],
                        #                   '--deamon',
                        ])
    if options.reload:
        server_cmd.append ('--reload')
    server_cmd.extend ([
            os.path.join(cfgopt['site_dir'], 'server.ini'),
            command,
            'services_enabled=%s' % cfgopt['services_enabled'],
            'services_disabled=%s' % cfgopt['services_disabled'],
            'http_port=%s' % cfgopt['port'],
            'http_host=%s' % cfgopt['host'],
            'rooturl=%s' % cfgopt['root'],
            #'proxyroot=%s' % cfgopt['proxyroot'],
            'sitecfg=%s' % cfgopt['site_cfg'],
            ])
    server_cmd.extend (args)
    verbose ('Executing: %s' % ' '.join(server_cmd))
    if not options.dryrun:
        processes.append(Popen(server_cmd))
    return processes

def mex_runner(command, options, processes, config):
    def verbose(msg):
        if options.verbose:
            print msg
        
    verbose('%s: %s' % (command , ' '.join(RUNNER_CMD)))
    if command is 'stop':
        if os.path.exists(os.path.join(config['pid_dir'], 'mexrunner.pid')):
            if not options.dryrun:
                f = open(os.path.join(config['pid_dir'], 'mexrunner.pid'), 'rb')
            mexrunner_pid = int(f.read())
            f.close()
            kill_process(mexrunner_pid)
            os.remove (os.path.join(config['pid_dir'], 'mexrunner.pid'))
            verbose("Stopped Mexrunner: %s" % mexrunner_pid)

    if command is 'start':
        if not options.dryrun:
            logfile = open(os.path.join(config['log_dir'], 'mexrunner.log'), 'wb')
            mexrunner = Popen(RUNNER_CMD, stdout=logfile, stderr=logfile)

            processes.append(mexrunner)
            open(os.path.join(config['pid_dir'], 'mexrunner.pid'), 'wb').write(str(mexrunner.pid))
            verbose("Starting Mexrunner: %s" % mexrunner.pid)
    
    return processes

def uwsgi_command(command, cfgopt, processes, options, default_cfg_file = None): 
    def verbose(msg):
        if options.verbose:
            print msg
            
    if command is 'stop':
        pidfile = cfgopt['pidfile']
        uwsgi_cmd = ['uwsgi', '--stop', pidfile]
        #processes.append(Popen(uwsgi_cmd,shell=True,stdout=sys.stdout))
        
        verbose('Executing: ' + ' '.join(uwsgi_cmd))
        if  call(uwsgi_cmd) != 0:
            print "Stop failed .. process already dead?"
        if os.path.exists (pidfile):
            os.remove (pidfile)
    elif command is 'start':
        cfg_file = find_site_cfg(default_cfg_file)
        final_cfg = os.path.join(os.path.dirname(cfg_file), default_cfg_file.replace('.default', ''))
        from string import Template
        t = Template(open(cfg_file, 'r').read())
        f = open(final_cfg, 'w')
        f.write(t.safe_substitute(cfgopt))
        f.close()
        
        uwsgi_cmd = ['uwsgi', '--ini-paste', final_cfg]

        #if cfgopt['http_serv'] == 'true':
        #    uwsgi_cmd.extend(['--http', cfgopt['url']])
        #processes.append(Popen(uwsgi_cmd,shell=True,stdout=sys.stdout))
        verbose('Executing: ' + ' '.join(uwsgi_cmd))
        if  call(uwsgi_cmd) != 0:
            print "Start failed"
    return processes
            

def operation(command, options, cfg_file=SITE_CFG, *args):
    """Run a multi-server command to start several bisque jobs
    """
    def verbose(msg):
        if options.verbose:
            print msg

    site_cfg = options.site or find_site_cfg(cfg_file)
    if site_cfg is None:
        print "Cannot find site.cfg.. please make sure you are in the bisque dir"
        return
    site_dir = os.path.dirname(os.path.abspath(site_cfg))

    verbose('using config : %s' % site_cfg)
    try:
        config = readhostconfig(site_cfg)
        verbose("ROOT %s SERVERS %s" % (config['root'], config['servers'].keys()))
        processes = []
        cfgopt = {'root': config['root']}
        cfgopt['site_dir'] = site_dir
        cfgopt['site_cfg'] = site_cfg
        cfgopt['virtualenv'] = os.getenv('VIRTUAL_ENV')          
        mexrun = asbool(config.get('mex_dispatcher', True))

        backend = config.get('backend', None)
        verbose("using backend: " + str(backend))
        
        if backend == None:
            verbose("Backend not configured. defaulting to paster")
            backend = 'paster'

        for key, serverspec in sorted(config['servers'].items()):
            cfgopt['server'] = serverspec.pop('server', None)
            cfgopt['url'] = serverspec.pop('url')
            fullurl = urlparse (cfgopt['url'])
            cfgopt['services_enabled'] = ','.join([
                l.strip() for l in serverspec.pop('services_enabled', '').split(',')])
            cfgopt['services_disabled'] = ','.join([
                l.strip() for l in serverspec.pop('services_disabled', '').split(',')])
            cfgopt['host'] = fullurl[1].split(':')[0]
            cfgopt['port'] = str(fullurl.port)
            #cfgopt['proxyroot'] = serverspec.pop('proxyroot', '')
            cfgopt['logfile'] = os.path.join(config['log_dir'], LOG_TEMPL % cfgopt['port'])
            cfgopt['pidfile'] = os.path.join(config['pid_dir'], PID_TEMPL % cfgopt['port'])

            if command in ('stop', 'restart'):
                if backend == 'uwsgi':
                    processes = uwsgi_command('stop', cfgopt, processes, options)
                else:
                    processes = paster_command('stop', options, cfgopt, processes, args)
                for proc in processes:
                    proc.wait()
                processes = []

            if command in ('start', 'restart'):
                if os.path.exists(cfgopt['pidfile']):
                    if options.force:
                        print 'old pid file: %s exists! restarting...' % cfgopt['pidfile']
                        operation("stop", options, cfg_file, *args)
                        time.sleep(5)
                    else:
                        sys.exit(2)
                if backend == 'uwsgi':
                    cfgopt["server"] = cfgopt['server'].replace('unix://','').strip()
                    if cfgopt['services_enabled'] == 'engine_service':
                        def_cfg = UWSGI_ENGINE_CFG
                    if cfgopt['services_disabled'] == 'engine_service':
                        def_cfg = UWSGI_CLIENT_CFG
                    if not find_site_cfg(def_cfg):
                        print ("Cannot find config file %s" % def_cfg)
                        return 
                    processes = uwsgi_command('start', cfgopt, processes, options, def_cfg)
                else:
                    prepare_log (cfgopt['logfile'])
                    processes = paster_command('start', options, cfgopt, processes, args)


        if mexrun and command in ('stop', 'restart'):
            mex_runner('stop', options, processes, config)
            for proc in processes:
                proc.wait()
            processes = []
        if mexrun and command in ('start', 'restart'):
            startmex = True
            # Should work, paster server returns 0 even when it fails
            for proc in processes:
                #print "checking %s" % proc
                proc.poll()
                if proc.returncode is not None and proc.returncode != 0:
                    print "Warning: %s failed" % proc
                    startmex = False
            if startmex:
                processes = mex_runner('start', options, processes, config)
        if options.wait:
            for proc in processes:
                proc.wait()

        #check for failed start


            #if command in ('start', 'restart'):
            #    time.sleep(5)
            #if command in ('start', 'restart'):
            #    LOG = open (logfile, 'rU')
            #    tail (LOG)
    except KeyboardInterrupt:
        pass
    except:
        raise



