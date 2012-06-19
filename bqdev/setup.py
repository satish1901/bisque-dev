try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '0.5.1'

setup(name='bqdev',
      version=version,
      description="Bisque Module API",
      author='Center for Bioimage informatics',
      author_email='cbi@biodev.ece.ucsb.edu',
      #home_page = 'http://biodev.ece.ucsb.edu/projects/bisque',
      url='http://biodeve.ece.ucsb.edu/projects/bisquik',
      packages= ['bq', 'bq.api' ],
      install_requires=[
        "httplib2",
        "lxml",
        ]
      )
