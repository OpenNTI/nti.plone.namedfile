#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import assert_that

import unittest

from plone.namedfile.schema import EncodingBytesLine

from plone.namedfile.tests import SharedConfiguringTestLayer


class TestSchema(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_validate(self):
        field = EncodingBytesLine()
        res = field.validate(u'abc')
        assert_that(res, is_(b'abc'))

    def test_fromUnicode(self):
        field = EncodingBytesLine()
        res = field.fromUnicode(u'abc')
        assert_that(res, is_(b'abc'))
