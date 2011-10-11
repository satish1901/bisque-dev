#!/usr/bin/env python
import sys
import os
from migrate.versioning.shell import main
import bq
from bq.core.commands.configfile import ConfigFile


# first pull initial values from config files
#iv = initial
tc = ConfigFile()      
if os.path.exists ('config/site.cfg'): 
    tc.read(open('config/site.cfg'))

db = tc.get('app:main', 'sqlalchemy.url')
if db is None:
    print "Please set sqlalchemy.url in site.cfg "

main(url=db, repository='bqcore/migration/')

