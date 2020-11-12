#!/usr/bin/env python
""" PyQRNative - generate QR codes in Python

svn2git converted http://pyqrnative.googlecode.com/svn/trunk/

Project home
------------

http://code.google.com/p/pyqrnative/

"""

#Upload to pypi::
#
#    python setup.py sdist --formats=gztar,zip upload


DOCLINES = __doc__.split("\n")

import os
import sys
import re
from distutils.core import setup


CLASSIFIERS = """\
License :: OSI Approved
Development Status :: 4 - Beta
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development
"""

NAME                = 'pyqrnative'
MAINTAINER          = "Sebastian F. Walter"
MAINTAINER_EMAIL    = "sebastian.walter@gmail.com"
DESCRIPTION         = DOCLINES[0]
LONG_DESCRIPTION    = "\n".join(DOCLINES[2:])
KEYWORDS            = ['qr code']
URL                 = "http://packages.python.org/qrnative"
DOWNLOAD_URL        = "http://www.github.com/b45ch1/qrnative"
LICENSE             = 'MIT'
CLASSIFIERS         = filter(None, CLASSIFIERS.split('\n'))
AUTHOR              = "Sam Curren"
AUTHOR_EMAIL        = "telegramsam@gmail.com"
PLATFORMS           = ["all"]
MAJOR               = 0
MINOR               = 1
MICRO               = 4
ISRELEASED          = True
VERSION             = '%d.%d.%d' % (MAJOR, MINOR, MICRO)


def write_version_py(filename='pyqrnative/version.py'):

    try:
        gitfile = open('.git/refs/heads/master', 'r')
        git_revision = '.dev' + gitfile.readline().split('\n')[0]

    except:
        git_revision = '.dev'

    cnt = """
# THIS FILE IS GENERATED FROM SETUP.PY
short_version = '%(version)s'
version = '%(version)s'
version_major = %(major)d
version_minor = %(minor)d
version_micro = %(micro)d
release = %(isrelease)s

if not release:
    version += '%(git_revision)s'
"""

    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': VERSION,
                        'major': MAJOR,
                        'minor': MINOR,
                        'micro': MICRO,
                        'isrelease': str(ISRELEASED),
                        'git_revision': git_revision
                      })
    finally:
        a.close()


def setup_package():

    # Rewrite the version file everytime
    write_version_py()
    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        author=AUTHOR,
        platforms=PLATFORMS,
        author_email=AUTHOR_EMAIL,
        keywords=KEYWORDS,
        url=URL,
        packages=['PyQRNative'],
     )


if __name__ == '__main__':
    setup_package()
