#!/usr/bin/env python

#import os,sys
#os.execvp ('paver', sys.argv)
from distutils2.core import setup
# try:
#     from setuptools import setup, find_packages
# except ImportError:
#     from ez_setup import use_setuptools
#     use_setuptools()
#     from setuptools import setup, find_packages




setup(name='bisque',
      version='0.5.1',
      description='Bisque suite',
      author='cbi',
      author_email='help@bioimage.ucsb.edu',
      home_page = 'http://biodev.ece.ucsb.edu/projects/bisque',
      url='http://biodeve.ece.ucsb.edu/projects/bisquik',
      packages=['bq', 'bqdev'],
      package_dir={'bq': 'bqcore/bq', 'bqdev' : 'bqdev/bqdev'},
      #package_dir = { 'bq':'bqcore' } ,
      #packages = ['bq', 'bq.core'],
      data_files = [ ('config', [ 'config/site.cfg.default' ])],
     )


