
from setuptools import setup, find_packages

setup(
    name='bqengine',
    version='0.0',
    description='',
    author='',
    author_email='',
    #url='',
    install_requires=["bqcore",
                      "httplib2",
                      'bbfreeze',
                      ],
    setup_requires=["PasteScript>=1.6.3"],
    paster_plugins=['PasteScript', 'Pylons' ],
    packages= find_packages(),
    namespace_packages = ['bq'],
    zip_safe = False,
    #include_package_data=True,
    test_suite='nose.collector',
    tests_require=['WebTest', 'BeautifulSoup'],
    package_data={'': ['*.html',]},
    message_extractors = {'bq': [
            ('**.py', 'python', None),
            ('templates/**.mako', 'mako', None),
            ('templates/**.html', 'genshi', None),
            ('public/**', 'ignore', None)]},

    entry_points="""
    [bisque.services]
    engine_service = bq.engine.controllers.engine_service
    [bq.commands]
    module = bq.engine.commands.module_admin:module_admin

    """,
)
