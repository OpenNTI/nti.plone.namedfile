#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Externalization Interfaces

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import schema
from zope import interface

from zope.schema.interfaces import IObject

HAVE_BLOBS = True


class ITextType(interface.Interface):
    """
    Marker interface for text type.
    """
interface.classImplements(six.text_type, ITextType)


class IBinaryType(interface.Interface):
    """
    Marker interface for binary types.
    """
interface.classImplements(six.binary_type, IBinaryType)


class IFile(interface.Interface):

    contentType = schema.BytesLine(
        title=u'Content Type',
        description=u'The content type identifies the type of data.',
        default=b'',
        required=False,
        missing_value=b''
    )

    data = schema.Bytes(
        title=u'Data',
        description=u'The actual content of the object.',
        default=b'',
        missing_value=b'',
        required=False,
    )

    def getSize():
        """
        Return the byte-size of the data of the object.
        """


class IImage(IFile):
    """
    This interface defines an Image that can be displayed.
    """

    def getImageSize():
        """
        Return a tuple (x, y) that describes the dimensions of
        the object.
        """

# Values


class INamed(interface.Interface):
    """
    An item with a filename
    """

    filename = schema.TextLine(title=u'Filename', required=False, default=None)


class INamedFile(INamed, IFile):
    """A non-BLOB file with a filename
    """


class INamedImage(INamed, IImage):
    """
    A non-BLOB image with a filename
    """


# Fields


class IStorage(interface.Interface):
    """
    Store file data
    """

    def store(data, blob):
        """
        Store the data into the blob
        Raises NonStorable if data is not storable.
        """


class NotStorable(Exception):
    """
    Data is not storable
    """


# Values


class IBlobby(interface.Interface):
    """
    Marker interface for objects that support blobs.
    """


class INamedBlobFile(INamedFile, IBlobby):
    """
    A BLOB file with a filename
    """


class INamedBlobImage(INamedImage, IBlobby):
    """
    A BLOB image with a filename
    """
