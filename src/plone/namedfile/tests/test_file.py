#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import has_property

import io
import unittest

import fudge

from ZODB.blob import BlobError

from plone.namedfile.file import MAXCHUNKSIZE

from plone.namedfile.file import FileChunk
from plone.namedfile.file import NamedFile
from plone.namedfile.file import NamedImage
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer


class TestFile(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _makeFile(self, *args, **kw):
        return NamedFile(*args, **kw)

    def _makeImage(self, *args, **kw):
        return NamedImage(*args, **kw)

    def _makeBlobFile(self, *args, **kw):
        return NamedBlobFile(*args, **kw)

    def _makeBlobImage(self, *args, **kw):
        return NamedBlobImage(*args, **kw)

    def test_filechunk(self):
        fc = FileChunk(b'zope')
        assert_that(fc[0], is_('z'))
        assert_that(str(fc), is_('zope'))

        fc.next = FileChunk(b'catalog')
        assert_that(bytes(fc), is_(b'zopecatalog'))

    def test_fileio(self):
        source = self._makeFile(filename=u'zptlogo.gif')
        data = getFile('zptlogo.gif')
        fileio = io.BytesIO(data)
        source._setData(fileio)
        assert_that(source.getSize(), is_(18920))

        source = self._makeFile()
        fileio = io.BytesIO(b'a' * MAXCHUNKSIZE)
        source._setData(fileio)
        assert_that(source.getSize(), is_(MAXCHUNKSIZE))

        # no jar
        source = self._makeFile()
        fileio = io.BytesIO(b'a' * MAXCHUNKSIZE * 3)
        source._setData(fileio)
        assert_that(source.getSize(), is_(MAXCHUNKSIZE * 3))

        # jar
        jar = fudge.Fake().provides('add').provides('register')
        source = self._makeFile()
        source._p_jar = jar
        fileio = io.BytesIO(b'a' * MAXCHUNKSIZE * 3)
        source._setData(fileio)
        assert_that(source.getSize(), is_(MAXCHUNKSIZE * 3))

    def test_coverage_file(self):
        source = self._makeFile()
        source._data = b'zope'
        assert_that(source,
                    has_property('data', is_(b'zope')))

        source._setData(u'zope')
        assert_that(source,
                    has_property('data', is_(b'zope')))

        with self.assertRaises(TypeError):
            source._setData(None)

        source._setData(FileChunk(b'zope'))
        assert_that(source,
                    has_property('data', is_(b'zope')))

    @fudge.patch('plone.namedfile.file.get_exif')
    def test_exif(self, mock_ge):
        import piexif
        mock_ge.is_callable().returns(
            {'0th': {piexif.ImageIFD.Orientation: 2}}
        )
        data = getFile('sample.jpg')
        image = self._makeImage(data=data)
        assert_that(image.getImageSize(), is_((500, 200)))

    def test_blob_file(self):
        source = self._makeBlobFile(data=b'zope')
        assert_that(source.getSize(), is_(4))

        fp = source.open('w')
        fp.write(b'catalog')
        fp.close()
        assert_that(source,
                    has_property('data', is_(b'catalog')))
        assert_that(source.getSize(), is_(7))

        with self.assertRaises(BlobError):
            source.openDetached()

        source._setData(b'index')
        assert_that(source,
                    has_property('data', is_(b'index')))

        assert_that(source,
                    has_property('size', is_(5)))

    @fudge.patch('plone.namedfile.file.get_exif')
    def test_blob_image(self, mock_ge):
        import piexif
        mock_ge.is_callable().returns(
            {'0th': {piexif.ImageIFD.Orientation: 2}}
        )
        data = getFile('zptlogo.gif')
        image = self._makeBlobImage(contentType=b'image/gif', data=data)
        assert_that(image,
                    has_property('contentType', is_(b'image/gif')))
        
        mock_ge.is_callable().returns(
            {'0th': {}}
        )
        data = getFile('zptlogo.gif')
        image = self._makeBlobImage(contentType=b'image/gif', data=data)
        assert_that(image.getImageSize(), is_((1536, 532)))

        image._width, image._height = (-1, -1)
        assert_that(image.getImageSize(), is_((1536, 532)))
