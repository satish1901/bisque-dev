# -*- coding: utf-8 -*-
#quckstarted Options:
#
# sqlalchemy: True
# auth:       sqlalchemy
# mako:       False
#
#

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='bqcore',
    version='0.5.0',
    description='',
    author='',
    author_email='',
    #url='',
    install_requires=[
        "TurboGears2 >= 2.1.1",
        "Genshi",
        "zope.sqlalchemy >= 0.4",
        "repoze.tm2 >= 1.0a5",
        "sqlalchemy",
        "sqlalchemy-migrate",
        "repoze.what-quickstart",
        "repoze.what >= 1.0.8",
        "repoze.what-quickstart",
        "repoze.who-friendlyform >= 1.0.4",
        "repoze.what-pylons >= 1.0",
        "repoze.what.plugins.sql",
        "repoze.who==1.0.19",
        "tgext.admin >= 0.3.9",
        "tw.forms",


        #"repoze.who.plugins.ldap",  #Optional for LDAP login
        #"repoze.who.plugins.openid",  #Optional for OpenID login
        

        # "TurboGears2 == 2.1.2",
        # "SQLAlchemy >= 0.7.2",      
        # "zope.sqlalchemy >= 0.4",
        # "repoze.tm2 >= 1.0a5",
        # "repoze.what-quickstart",
        # "repoze.what >= 1.0.8",
        # "repoze.what-quickstart",
        # "repoze.who-friendlyform >=1.0.4",
        # "repoze.what-pylons >= 1.0rc3",
        # "repoze.what.plugins.sql",
        # "repoze.who ==1.0.18",
        # #"repoze.who.plugins.ldap",  #Optional
        # "tgext.admin>=0.3.9",
        # "tw.forms",
        #########################
        # Bisque dependencies
        "lxml",
        "ply",
        "gdata",
        "Turbomail",
        "genshi",
        "TGScheduler",
        "boto",
        "numpy==1.6.0",
        # Installed from http://biodev.ece.ucsb.edu/binaries/depot
        "tw.recaptcha",
        "tgext.registration2",
        "tw.output", #https://bitbucket.org/alexbodn/twoutput/get/af6904c504cf.zip
        ],
    setup_requires=["PasteScript >= 1.7"],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2'],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['WebTest',
                   'Nose',
                   'coverage',
                   'wsgiref',
                   'repoze.who-testutil',
                   ],
    package_data={'bq': ['core/i18n/*/LC_MESSAGES/*.mo',
                                 'core/templates/*/*',
                                 'core/public/*/*']},

    scripts = ["scripts/bq-upload-images",
               "scripts/bqdev-upload-binary",
               ],
    
    message_extractors={'bq': [
            ('**.py', 'python', None),
            ('core/templates/**.mako', 'mako', None),
            ('core/templates/**.html', 'genshi', None),
            ('core/public/**', 'ignore', None)]},

    entry_points="""
    [paste.app_factory]
    main = bq.config.middleware:make_app

    [paste.filter_factory]
    add_global = bq.config.middleware:add_global

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    [console_scripts]
    bq-admin = bq.core.commands.admin:main
    mexrunner = bq.core.commands.mexrunner:main

    [bq.commands]
    servers = bq.core.commands.admin:servers
    setup   = bq.core.commands.admin:setup
    sql     = bq.core.commands.admin:sql

    [bisque.services]
    client_service   = bq.client_service.controllers.service
    auth_service     = bq.client_service.controllers.auth_service
    admin            = bq.client_service.controllers.admin_service
    notebook_service = bq.client_service.controllers.dn_service
    data_service     = bq.data_service.controllers.data_service
    #blob_service     = bq.blob_service.controllers.blobserver
    image_service    = bq.image_service.controllers.service
    stats            = bq.stats.controllers.stats_server
    analysis         = bq.module_service.controllers.analysis_server
    module_service   = bq.module_service
    export           = bq.export_service.controllers.export_service
    import           = bq.import_service.controllers.import_service
    registration     = bq.registration.controllers.registration_service
    ingest_service   = bq.ingest.controllers.ingest_server
    dataset_service  = bq.dataset_service.controllers.dataset_service
    """,
)
