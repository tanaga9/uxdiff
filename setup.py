#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from distutils.core import setup

__author__ =  'Tanaga'
__version__=  '1.5.0'

META_INFO = {
    'version'     : __version__,
    'license'     : 'MIT',
    'author'      : __author__,
    'email'       : 'tanaga9(@)users(.)noreply(.)github(.)com',
    'url'         : 'https://github.com/tanaga9/uxdiff',
    'keywords'    : 'colored side-by-side diff',
    'description' : ('As a command, Compare two text files or directories. '
                     'Improve text comparison in GUI-less environments. '
                     'Also, as a module, Compare and output a list of differences '
                     'between any two sequences of hashable objects.')
}

if sys.hexversion < 0x02070000:
    raise SystemExit("*** Requires python >= 2.7.0")

setup(
    name='uxdiff',
    version=META_INFO['version'],
    author=META_INFO['author'],
    author_email=META_INFO['email'].replace('(', '').replace(')', ''),
    license=META_INFO['license'],
    description=META_INFO['description'],
    keywords=META_INFO['keywords'],
    url=META_INFO['url'],
    py_modules=['uxdiff'],
    scripts=['uxdiff'],
    install_requires=[
        'unidiff>=0.6.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
