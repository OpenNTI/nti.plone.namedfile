#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries

import unittest
from six import StringIO

import fudge

import piexif

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer

from plone.namedfile.utils import get_exif
from plone.namedfile.utils import ensure_data
from plone.namedfile.utils import getImageInfo
from plone.namedfile.utils import rotate_image
from plone.namedfile.utils import safe_basename
from plone.namedfile.utils import get_contenttype

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

    def test_get_contenttype(self):
        assert_that(get_contenttype(),
                    is_('application/octet-stream'))

    def test_ensure_data(self):
        assert_that(ensure_data(StringIO(u'data')),
                    is_(b'data'))

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

    @fudge.patch('plone.namedfile.utils.Image')
    def test_get_image_info_invalid_image(self, mock_img):
        mock_img.provides('open').raises(Exception())
        assert_that(getImageInfo(b'xxxx'),
                    is_(('', -1, -1)))

    @fudge.patch('plone.namedfile.utils.Image')
    def test_get_image_info_pil_tiff(self, mock_img):
        info = fudge.Fake().has_attr(size=(10, 10)).has_attr(format='TIFF')
        mock_img.provides('open').returns(info)
        assert_that(getImageInfo(b'xxxx'),
                    is_(('image/tiff', 10, 10)))

    def test_get_exif(self):
        assert_that(get_exif(getFile('sample.jpg')),
                    has_entries('0th', {},
                                '1st', {},
                                'Exif', {},
                                'GPS', {}))

    @fudge.patch('plone.namedfile.utils.getImageInfo')
    def test_invalid_exif(self, mock_gi):
        mock_gi.is_callable().returns(('image/jpeg', 10, 10))
        assert_that(get_exif(b'xxxxxx'),
                    has_entries('0th',  {
                        piexif.ImageIFD.XResolution: (10, 1),
                        piexif.ImageIFD.YResolution: (10, 1)
                    }))

    def test_rotate_image(self):
        original = getFile('exif.jpg')
        data, width, height, exif_data = rotate_image(original)
        assert_that(width, is_(480))
        assert_that(height, is_(360))
        assert_that(data, has_length(32473))
        assert_that(sorted(exif_data.keys()),
                    is_(['0th', '1st', 'Exif', 'GPS', 'Interop', 'thumbnail']))

        for method in range(1, 9):
            rotate_image(original, method)

    @fudge.patch('plone.namedfile.utils.load_exif',
                 'plone.namedfile.utils.img_exif_data')
    def test_corrupt_exif(self, mock_pie, mock_ied):
        data = getFile('exif.jpg')
        mock_pie.is_callable().raises(ValueError())
        mock_ied.is_callable().returns({
            '0th': {
                piexif.ImageIFD.XResolution: None,
                piexif.ImageIFD.YResolution: None,
            }
        })
        data, width, height, exif_data = rotate_image(data, 5)
        assert_that(width, is_(360))
        assert_that(height, is_(480))
        assert_that(data, has_length(25736))
        assert_that(exif_data,
                    has_entries('0th',
                                has_entries(piexif.ImageIFD.XResolution, (360, 1),
                                            piexif.ImageIFD.YResolution, (480, 1),
                                            piexif.ImageIFD.Orientation, 1)))

    @fudge.patch('plone.namedfile.utils.load_exif')
    def test_no_exif_resolution(self, mock_pie):
        data = getFile('exif.jpg')
        mock_pie.is_callable().returns({'0th': {}})
        _, _, _, exif_data = rotate_image(data, method=5)
        assert_that(exif_data,
                    has_entries('0th',
                                has_entries(piexif.ImageIFD.XResolution, (360, 1),
                                            piexif.ImageIFD.YResolution, (480, 1))))

    @fudge.patch('plone.namedfile.utils.load_exif')
    def test_dump_error(self, mock_pie):
        data = getFile('exif.jpg')
        exif_data = {
            '0th': {
                piexif.ImageIFD.XResolution: (480, 1),
                piexif.ImageIFD.YResolution: (360, 1),
            },
            'Exif': {
                piexif.ExifIFD.SceneType: None
            }
        }
        mock_pie.is_callable().returns(exif_data)
        _, width, height, _ = rotate_image(data, method=5)
        assert_that(width, is_(360))
        assert_that(height, is_(480))
