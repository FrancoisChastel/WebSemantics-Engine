#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Common structures.
"""

from __future__ import with_statement, print_function, division

from collections import namedtuple

Node = namedtuple('Node',
                  ['id',
                   'label',
                   'img',
                   'url'])

Link = namedtuple('Link',
                  ['source',
                   'target',
                   'value',
                   'optionnal_label'])