
import os
from setuptools import setup
from setuptools.dist import Distribution

from paver.easy import path, Bunch

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


from setuptools.dist import Distribution
class PureDistribution(Distribution):
    def is_pure(self):
        return True

VERSION = '0.5.7'


def generate_data_files (toplevel, filters=None):
    'make a pair (dir, [list-of-files] ) for all dirs in toplevel'
    return ([ (toplevel, list (path(toplevel).walkfiles())) ]
            + [ (str(d), list ( d.walkfiles())) for d in path(toplevel).walkdirs() ])


setup(
    name='bisque',
    version=VERSION,
    author="Center for BioImage Informatics, UCSB",
    author_email = "info@bioimage.ucsb.edu",
    distclass = PureDistribution,
    classifiers = [
        'Private :: Do Not Upload',
#        "Development Status :: 5 - Production/Stable",
#        "Framework :: TurboGears :: Applications",
#        "Topic :: Scientific/Engineering :: Bio-Informatics",
#        "License :: OSI Approved :: BSD License",
        ],
    #package_data=find_package_data(),
    include_package_data = True,
    data_files =  generate_data_files ('./contrib') +  generate_data_files ('./config'),
    #packages=find_packages(exclude=['ez_setup']),
    #packages=["bq"],
    zip_safe=False,
    setup_requires=["PasteScript >= 1.7"],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2', 'bqengine'],
    #build_top=path("build"),
    #        build_dir=lambda: options.build_top / "bisque05",
    license=Bunch(
        extensions = set([
                ("py", "#"), ("js", "//")
                ]),
        exclude=set([
                './ez_setup',
                './data',
                './tg2env',
                './docs',
                # Things we don't want to add our license tag to
                ])
        ),
    )
