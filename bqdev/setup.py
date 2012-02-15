from setuptools import setup, find_packages
import sys, os

version = '0.5.1'

setup(name='bqdev',
      version=version,
      description="Bisque Module API",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Center for Bioimage informatics',
      author_email='cbi@biodev.ece.ucsb.edu',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
