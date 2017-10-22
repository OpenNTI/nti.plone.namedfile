#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

import fudge
import unittest

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer

from plone.namedfile.utils import safe_basename

from plone.namedfile.utils.jpeg_utils import process_jpeg

from plone.namedfile.utils.png_utils import process_png

from plone.namedfile.utils.tiff_utils import process_tiff


class TestUtils(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_safe_basename(self):
        assert_that(safe_basename('/farmyard/cows/daisy'),
                    is_('daisy'))

        assert_that(safe_basename('F:\FARMYARD\COWS\DAISY.TXT'),
                    is_('DAISY.TXT'))
        
        assert_that(safe_basename('Macintosh Farmyard:Cows:Daisy Text File'),
                    is_('Daisy Text File'))

    def test_png(self):
        data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x10\x00\x00\x00\x0f'
        assert_that(process_png(data),
                    is_(('image/png', 16, 15)))
        
    def test_invalid_jpeg(self):
        data = b'\377\330\r\n\x1a\n\x00\x0f'
        assert_that(process_jpeg(data),
                    is_(('image/jpeg', -1, -1)))
        
    @fudge.patch('plone.namedfile.utils.tiff_utils._tiff_type')
    def test_invalid_tiff_type(self, mock_tt):
        mock_tt.is_callable().returns(-1)
        data = getFile('sample.tiff')
        assert_that(process_tiff(data),
                    is_((None, -1, -1)))
