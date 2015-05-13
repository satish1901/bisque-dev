
from setuptools import setup
setup(name='bisque_ops',
      version='1.0',
      install_requires = [
        'requests',
        'argparse'
        ],

      py_modules = ['bisque_ops' ],

      entry_points = {
        'console_scripts' : [
            'bqpath = bisque_ops:main',
            ]
        }

      )

