#!/usr/bin/env python

#import os,sys
#os.execvp ('paver', sys.argv)

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages




setup(name='bisque',
      version='0.5.0',
      description='Bisque suite',
      author='cbi',
      author_email='help@bioimage.ucsb.edu',
      url='http://biodeve.ece.ucsb.edu/projects/bisquik',
      packages=['bq', 'bqdev'],
      package_dir={'bq': 'bqcore/bq', 'bqdev' : 'bqdev/bqdev'},
     )


