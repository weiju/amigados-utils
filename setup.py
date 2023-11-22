import os
import re
import codecs
from setuptools import setup

NAME = 'amigados-utils'
PACKAGES = ['amigados']
DESCRIPTION = 'amigados-utils is a collection of utilities for Amiga system development'
LICENSE = 'GPL V3'
URI = 'https://github.com/weiju/amigados-utils'
AUTHOR = 'Wei-ju Wu'
VERSION = '0.1.0'

KEYWORDS = ['amiga', 'system', 'development', 'classic', 'ecs', 'aga']

# See trove classifiers
# https://testpypi.python.org/pypi?%3Aaction=list_classifiers

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Software Development :: Libraries :: Python Modules"
    ]
INSTALL_REQUIRES = ['pillow', 'Jinja2']

PACKAGE_DATA = {
    'amigados': []
}

if __name__ == '__main__':
    setup(name=NAME, description=DESCRIPTION,
          license=LICENSE,
          url=URI,
          version=VERSION,
          author=AUTHOR,
          author_email='weiju.wu@gmail.com',
          maintainer=AUTHOR,
          maintainer_email='weiju.wu@gmail.com',
          keywords=KEYWORDS,
          packages=PACKAGES,
          zip_safe=False,
          classifiers=CLASSIFIERS,
          install_requires=INSTALL_REQUIRES,
          include_package_data=True, package_data=PACKAGE_DATA,
          scripts=['bin/amigados-png2image', 'bin/amigados-fdtool',
                   'bin/amigados-dalf', 'bin/amigados-bumprev',
                   'bin/amigados-dir', 'bin/amigados-copy'])
