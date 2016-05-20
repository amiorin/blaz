#!/usr/bin/env python

from setuptools import setup
from version import __version__

setup(name='blaz',
      version=__version__,
      description='Composable tasks inside docker containers',
      author='Alberto Miorin',
      author_email='alberto.miorin@gmail.com',
      url='https://github.com/amiorin/blaz',
      license='MIT',
      py_modules=['blaz', 'version'],
      install_requires=['ansicolors'],
      )
