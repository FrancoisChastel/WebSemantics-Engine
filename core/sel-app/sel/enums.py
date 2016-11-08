#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
All enumerations are here.
"""

from six import add_metaclass


class MetaEnum(type):
    def __repr__(cls):
        return 'Enum([{0}])'.format(', '.join(
            repr(a) for a in cls.__dict__ if not a.startswith('_')
        ))

@add_metaclass(MetaEnum)
class Enum(object):
    pass

""" Sample
class Encoding(Enum):
    unknown = '?'
    EDIFACT = 'EDI'
    XML = 'XML'
""" 
