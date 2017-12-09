#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import assert_that

import os
import tempfile
import unittest

from ZODB.blob import Blob

from plone.namedfile.file import FileChunk
from plone.namedfile.file import NamedBlobImage

from plone.namedfile.interfaces import NotStorable

from plone.namedfile.storages import BinaryStorable
from plone.namedfile.storages import UnicodeStorable
from plone.namedfile.storages import FileChunkStorable
from plone.namedfile.storages import FileDescriptorStorable

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer


class TestStorable(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_binary_storable(self):
        fi = NamedBlobImage(getFile('image.gif'), filename=u'image.gif')
        assert_that(fi.getSize(), is_(303))

    def test_filechunk_storable(self):
        fi = NamedBlobImage(FileChunk(getFile('image.gif')),
                            filename=u'image.gif')
        assert_that(fi.getSize(), is_(303))
        
    def test_filedescriptor_storable(self):
        name = tempfile.mktemp('.gif', 'image_')
        with open(name, "wb") as fp:
            fp.write(getFile('image.gif'))
        assert_that(os.path.exists(name), is_(True))
        with open(name, 'rb') as fp:
            blob = Blob()
            FileDescriptorStorable().store(fp, blob)
        assert_that(os.path.exists(name), is_(False))
        
    def test_coverage(self):
        with self.assertRaises(NotStorable):
            BinaryStorable().store(u'data', None)
        
        with self.assertRaises(NotStorable):
            UnicodeStorable().store(b'data', None)

        with self.assertRaises(NotStorable):
            FileChunkStorable().store(u'data', None)
            
        with self.assertRaises(NotStorable):
            FileDescriptorStorable().store(u'data', None)
