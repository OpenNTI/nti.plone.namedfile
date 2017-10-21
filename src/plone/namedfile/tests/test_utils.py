#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

import unittest

from plone.namedfile.tests import SharedConfiguringTestLayer

from plone.namedfile.utils.jpeg_utils import process_jpeg

from plone.namedfile.utils.png_utils import process_png

class TestUtils(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_png(self):
        data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x10\x00\x00\x00\x0f'
        assert_that(process_png(data),
                    is_(('image/png', 16, 15)))
        
    def test_invalid_jpeg(self):
        data = b'\377\330\r\n\x1a\n\x00\x0f'
        assert_that(process_jpeg(data),
                    is_(('image/jpeg', -1, -1)))
