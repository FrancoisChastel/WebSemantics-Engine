#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Packaging
"""

from __future__ import with_statement
import sys
from setuptools import setup, find_packages

with open('VERSION') as f:
    VERSION = f.read().rstrip()

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

INSTALL_REQUIRES = [
	'six==1.10.0',
]

if sys.version_info[0] < 3:
    INSTALL_REQUIRES += [
        'Counter==1.0.0',
        'pyparsing<2.0.0',
        'pydot2==1.0.33',
    ]
else:  # Python 3+
    INSTALL_REQUIRES += [
        'pydot==1.2.2',
    ]

setup(
    name='Semantics-Engine Learning',
    version=VERSION,
    author='Frnaçois Chastel',
    author_email='francois@chastel.co',
    url='https://github.com/FrancoisChastel/WebSemantics-Engine.git',
    description='A library that render semantics respinses with learning part.',
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts' : [
            'sel=selmain:main',
        ],
    },
)
