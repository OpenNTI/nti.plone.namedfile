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

import unittest

from zope.interface.verify import verifyClass

from plone.namedfile.file import NamedImage

from plone.namedfile.interfaces import INamedImage

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer

from plone.namedfile.utils import get_contenttype

zptlogo = getFile('zptlogo.gif')


class TestImage(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _makeImage(self, *args, **kw):
        return NamedImage(*args, **kw)

    def testEmpty(self):
        file_img = self._makeImage()
        assert_that(file_img,
                    has_properties('contentType', is_(''),
                                   'data', is_(b'')))

    def testConstructor(self):
        file_img = self._makeImage(b'Data')
        assert_that(file_img,
                    has_properties('contentType', is_(''),
                                   'data', is_(b'Data')))

    def testMutators(self):
        image = self._makeImage()
        image.contentType = 'image/jpeg'
        assert_that(image, 
                    has_property('contentType', 'image/jpeg'))

        image._setData(zptlogo)
        assert_that(image,
                    has_properties('data', equal_to(zptlogo),
                                   'contentType', is_('image/gif')))
       
        assert_that(image.getImageSize(), is_((1536, 532)))

    def testInterface(self):
        self.assertTrue(INamedImage.implementedBy(NamedImage))
        self.assertTrue(verifyClass(INamedImage, NamedImage))

    def test_get_contenttype(self):
        assert_that(get_contenttype(NamedImage(getFile('image.gif'),
                                               contentType='image/gif')),
                    is_('image/gif'))

        assert_that(get_contenttype(NamedImage(getFile('image.gif'),
                                               filename=u'image.gif')),
                    is_('image/gif'))

        assert_that(get_contenttype(NamedImage(getFile('notimage.doc'),
                                               filename=u'notimage.doc')),
                    is_('application/msword'))
