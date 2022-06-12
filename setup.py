#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from distutils.core import setup

__author__ =  'Tanaga'
__version__=  '1.4.5'

META_INFO = {
    'version'     : __version__,
    'license'     : 'MIT',
    'author'      : __author__,
    'email'       : 'tanaga9(@)users(.)noreply(.)github(.)com',
    'url'         : 'https://github.com/tanaga9/uxdiff',
    'keywords'    : 'colored side-by-side diff',
    'description' : ('Compare two text files or directories.'
                     'Improves text comparison in GUI-less environments.')
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
)
