
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

#from bq.release import __VERSION__
__VERSION__="0.5.5"

setup(
    name='bqfeature',
    version=__VERSION__,
    description='',
    author='',
    author_email='',
    #url='',
    install_requires=[
                      "importlib", #not needed for python 2.7
                      "bqcore",
                      "numpy",
                      "pillow",
                      "mahotas",  
                      "tables",  
                      "numexpr",
                      "cython",  
                      #"opencv", 
                      ],
    setup_requires=["PasteScript>=1.6.3"],
    paster_plugins=['PasteScript', 'Pylons' ],
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages = ['bq'],
    zip_safe = False,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['WebTest', 'BeautifulSoup'],
    package_data={'bq': ['i18n/*/LC_MESSAGES/*.mo', 'templates/*',]},
    message_extractors = {'bq': [
            ('**.py', 'python', None),
            ('templates/**.mako', 'mako', None),
            ('templates/**.html', 'genshi', None),
            ('public/**', 'ignore', None)]},

    entry_points="""
    [bisque.services]
      features = bq.features.controllers.service
    """,
)
