#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from distutils.core import setup
from udiff import META_INFO as _meta

if sys.hexversion < 0x02070000:
    raise SystemExit("*** Requires python >= 2.7.0")

setup(
    name='udiff',
    version=_meta['version'],
    author=_meta['author'],
    author_email=_meta['email'].replace('(', '').replace(')', ''),
    license=_meta['license'],
    description=_meta['description'],
    keywords=_meta['keywords'],
    url=_meta['url'],
    py_modules=['udiff'],
    scripts=['udiff'],
)
