#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import unittest

from plone.namedfile.file import FileChunk
from plone.namedfile.file import NamedBlobImage

from plone.namedfile.tests import getFile
from plone.namedfile.tests import SharedConfiguringTestLayer


class TestStorable(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_binary_storable(self):
        fi = NamedBlobImage(getFile('image.gif').read(), filename=u'image.gif')
        self.assertEqual(303, fi.getSize())

    def test_filechunk_storable(self):
        fi = NamedBlobImage(FileChunk(getFile('image.gif').read()),
                            filename=u'image.gif')
        self.assertEqual(303, fi.getSize())
