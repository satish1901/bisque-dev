from setuptools import setup, find_packages
import sys, os

#from bq.release import __VERSION__
__VERSION__ = '0.5.3'

setup(name='bqserver',
      version=__VERSION__,
      description="Main Bisque server",
      long_description="""\
The bisque server
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='bioinformatics, image, database',
      author='Center for Bioinformatics',
      author_email='cbi@biodev.ece.ucsb.edu',
      url='http://bioimage.ucsb.edu',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
#        "bqcore",
        "ply",
        "gdata",
        "Turbomail",
        "genshi",
        "TGScheduler",
        "boto",
        "numpy",
        "ordereddict",
        # Installed from http://biodev.ece.ucsb.edu/binaries/depot
        "tw.recaptcha",
        "tgext.registration2",
        "tw.output", #https://bitbucket.org/alexbodn/twoutput/get/af6904c504cf.zip
        "mahotas",  # Feature
        "tables==3.0.0",  # Feature
        "numexpr==1.4.2", # Feature
        "cython",  # Feature
        #"opencv",  # Feature        
        # "importlib", # Feature, not needed for python 2.7
        "furl",
      ],
      entry_points="""
      # -*- Entry points: -*-
    [bisque.services]
    client_service   = bq.client_service.controllers.service
    auth_service     = bq.client_service.controllers.auth_service
    admin            = bq.client_service.controllers.admin_service
    notebook_service = bq.client_service.controllers.dn_service
    data_service     = bq.data_service.controllers.data_service
    blob_service     = bq.blob_service.controllers.blobsrv
    image_service    = bq.image_service.controllers.service
    stats            = bq.stats.controllers.stats_server
    module_service   = bq.module_service.controllers.module_server
    export           = bq.export_service.controllers.export_service
    import           = bq.import_service.controllers.import_service
    registration     = bq.registration.controllers.registration_service
    ingest_service   = bq.ingest.controllers.ingest_server
    dataset_service  = bq.dataset_service.controllers.dataset_service
    usage            = bq.usage.controllers.usage
    features         = bq.features.controllers.features	

    [bq.commands]
    module = bq.module_service.commands.module_admin:module_admin
      """,
      )
