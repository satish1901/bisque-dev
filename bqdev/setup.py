from setuptools import setup, find_packages
import sys, os

version = '0.5.0'

setup(name='bqdev',
      version=version,
      description="Bisque Development Utilities",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
        "virtualenv",
        "poster"
      ],



      entry_points="""
      # -*- Entry points: -*-
      [bq.commands]
      create-core    = bqdev.commands.create:createCoreService
      create-service = bqdev.commands.create:createService
      create-module = bqdev.commands.create:createModule
      create-bootstrap = bqdev.commands.create_bootstrap:make_bootstrap
      
      [paste.paster_create_template]
      bisque_core = bqdev.bisque_template:CoreServiceTemplate
      bisque_service = bqdev.bisque_template:ServiceTemplate
      bisque_module = bqdev.bisque_template:ModuleTemplate
      """,
      )
