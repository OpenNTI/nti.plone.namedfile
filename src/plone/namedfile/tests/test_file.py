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

from plone.namedfile.file import MAXCHUNKSIZE

from plone.namedfile.file import FileChunk
from plone.namedfile.file import NamedFile

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer


class TestFile(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _makeFile(self, *args, **kw):
        return NamedFile(*args, **kw)

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
