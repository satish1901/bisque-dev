try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

#from bq.release import __VERSION__
__VERSION__="0.5.9"

setup(name='bqapi',
      version=__VERSION__,
      description="Bisque Module API",
      author='Center for Bioimage informatics',
      author_email='cbi@biodev.ece.ucsb.edu',
      #home_page = 'http://biodev.ece.ucsb.edu/projects/bisque',
      url='http://biodeve.ece.ucsb.edu/projects/bisquik',
      packages= find_packages(), # ['bqapi', 'bqapi. ],
      ###packages= ['bqapi' ],
#      namespace_packages = ['bq'],
      install_requires=[
          "requests >=2.4.1",
          "requests_toolbelt >= 0.6.2",
        ],
      extras_require = {
          'lxml' : [ 'lxml'],
          'CAS'  : ['BeautifulSoup4' ],
          'bqfeature' : ['tables'],
      },

      zip_safe= True,
  )
