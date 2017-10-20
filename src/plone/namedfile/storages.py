#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file was borrowed from z3c.blobfile and is licensed under the terms of
the ZPL.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope.interface import implementer

from plone.namedfile.file import FileChunk

from plone.namedfile.interfaces import IStorage
from plone.namedfile.interfaces import NotStorable

MAXCHUNKSIZE = 1 << 16

logger = __import__('logging').getLogger(__name__)


@implementer(IStorage)
class BinaryStorable(object):

    def store(self, data, blob):
        if not isinstance(data, six.binary_type):
            raise NotStorable('Could not store data (not of "bytes" type).')

        with blob.open('w') as fp:
            fp.write(data)
StringStorable = BinaryStorable


@implementer(IStorage)
class UnicodeStorable(StringStorable):

    def store(self, data, blob):
        if not isinstance(data, six.text_type):
            raise NotStorable('Could not store data (not of "unicode" type).')

        data = data.encode('utf-8')
        StringStorable.store(self, data, blob)


@implementer(IStorage)
class FileChunkStorable(object):

    def store(self, data, blob):
        if not isinstance(data, FileChunk):
            raise NotStorable('Could not store data (not a of "FileChunk" type).')  # noqa

        with blob.open('w') as fp:
            chunk = data
            while chunk:
                fp.write(chunk, '_data')
                chunk = chunk.next


@implementer(IStorage)
class FileDescriptorStorable(object):

    def store(self, data, blob):
        if not isinstance(data, file):
            raise NotStorable('Could not store data (not of "file").')

        filename = getattr(data, 'name', None)
        if filename is not None:
            blob.consumeFile(filename)
            return
