#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import equal_to
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import has_properties

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import struct
import unittest

import transaction

from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage

from plone.namedfile.interfaces import INamedBlobFile
from plone.namedfile.interfaces import INamedBlobImage

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer


class TestImage(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _makeImage(self, *args, **kw):
        return NamedBlobImage(*args, **kw)

    def testEmpty(self):
        image = self._makeImage()
        assert_that(image, 
                    has_properties('contentType', b'',
                                   'data', b''))

    def testConstructor(self):
        image = self._makeImage(b'Data')
        assert_that(image, 
                    has_properties('contentType', b'',
                                   'data', b'Data'))

    def testMutators(self):
        image = self._makeImage()

        image.contentType = 'image/jpeg'
        assert_that(image, 
                    has_property('contentType', 'image/jpeg'))

        zptlogo = getFile('zptlogo.gif')
        image._setData(zptlogo)
        assert_that(image,
                    has_properties('data', equal_to(zptlogo),
                                   'contentType', is_('image/gif')))
        assert_that(image.getImageSize(), is_((1536, 532)))

    def testInterface(self):
        image = self._makeImage()
        
        assert_that(image, validly_provides(INamedBlobFile))
        assert_that(image, verifiably_provides(INamedBlobFile))
        
        assert_that(image, validly_provides(INamedBlobImage))
        assert_that(image, verifiably_provides(INamedBlobImage))
 
    def testDataMutatorWithLargeHeader(self):
        from plone.namedfile.file import IMAGE_INFO_BYTES
        bogus_header_length = struct.pack('>H', IMAGE_INFO_BYTES * 2)
        data = (b'\xff\xd8\xff\xe0' + bogus_header_length +
                b'\x00' * IMAGE_INFO_BYTES * 2 +
                b'\xff\xc0\x00\x11\x08\x02\xa8\x04\x00')
        image = self._makeImage()
        image._setData(data)
        self.assertEqual(image.getImageSize(), (1024, 680))


class TestImageFunctional(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def testCopyBlobs(self):
        from zope.copy import copy
        source = NamedBlobFile()
        source.data = u'hello, world'

        image = NamedBlobImage()
        image.data = 'some image bytes'
        transaction.commit()

        file_copy = copy(source)
        assert_that(file_copy.data, is_(source.data))

        image_copy = copy(image)
        assert_that(image_copy.data, is_(image.data))
