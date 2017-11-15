#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import interface

from zope.schema import BytesLine

from zope.schema.interfaces import IFromUnicode


@interface.implementer(IFromUnicode)
class EncodingBytesLine(BytesLine):
    """
    A byte lines type that will attempt to encode string data.
    """

    def validate(self, value):
        if isinstance(value, six.string_types):
            value = value.encode('utf-8')
        super(EncodingBytesLine, self).validate(value)
        return value  # tests

    def fromUnicode(self, value):
        if isinstance(value, six.string_types):
            return value.encode('utf-8')
        return value
