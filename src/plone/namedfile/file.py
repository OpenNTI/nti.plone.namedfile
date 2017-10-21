#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The implementations in this file are largely borrowed
from zope.app.file and z3c.blobfile
and are licensed under the ZPL.

.. $Id$
"""

import six

from persistent import Persistent

from ZODB.blob import Blob

from zope.component import getUtility

from zope.interface import implementer

from zope.schema.fieldproperty import FieldProperty

import piexif

import transaction

from plone.namedfile.interfaces import IStorage
from plone.namedfile.interfaces import INamedFile
from plone.namedfile.interfaces import INamedImage
from plone.namedfile.interfaces import INamedBlobFile
from plone.namedfile.interfaces import INamedBlobImage

from plone.namedfile.utils import get_exif
from plone.namedfile.utils import getImageInfo
from plone.namedfile.utils import rotate_image
from plone.namedfile.utils import get_contenttype

MAXCHUNKSIZE = 1 << 16

IMAGE_INFO_BYTES = 1024

MAX_INFO_BYTES = 1 << 16

logger = __import__('logging').getLogger(__name__)


class FileChunk(Persistent):
    """
    Wrapper for possibly large data
    """

    next = None

    def __init__(self, data):
        self._data = data

    def __getitem__(self, i):
        return self._data[i]

    def __len__(self):
        data = bytes(self)
        return len(data)

    def __bytes__(self):
        next_ = self.next
        if next_ is None:
            return self._data
        result = [self._data]
        while next_ is not None:
            self = next_
            result.append(self._data)
            next_ = self.next
        return b''.join(result)

    if str is bytes:
        __str__ = __bytes__
    else:
        def __str__(self):
            return self.__bytes__().decode("iso-8859-1", errors='ignore')


FILECHUNK_CLASSES = [FileChunk]
try:
    from zope.app.file.file import FileChunk as Zope_FileChunk
    FILECHUNK_CLASSES.append(Zope_FileChunk)
except ImportError:
    pass
FILECHUNK_CLASSES = tuple(FILECHUNK_CLASSES)


@implementer(INamedFile)
class NamedFile(Persistent):
    """
    A non-BLOB file that stores a filename

    Let's test the constructor:

    >>> file = NamedFile()
    >>> file.contentType
    ''
    >>> file.data
    ''

    >>> file = NamedFile('Foobar')
    >>> file.contentType
    ''
    >>> file.data
    'Foobar'

    >>> file = NamedFile('Foobar', 'text/plain')
    >>> file.contentType
    'text/plain'
    >>> file.data
    'Foobar'

    >>> file = NamedFile(data='Foobar', contentType='text/plain')
    >>> file.contentType
    'text/plain'
    >>> file.data
    'Foobar'


    Let's test the mutators:

    >>> file = NamedFile()
    >>> file.contentType = 'text/plain'
    >>> file.contentType
    'text/plain'

    >>> file.data = 'Foobar'
    >>> file.data
    'Foobar'

    >>> file.data = None
    Traceback (most recent call last):
    ...
    TypeError: Cannot set None data on a file.


    Let's test large data input:

    >>> file = NamedFile()

    Insert as string:

    >>> file.data = 'Foobar'*60000
    >>> file.getSize()
    360000
    >>> file.data == 'Foobar'*60000
    True

    Insert data as FileChunk:

    >>> fc = FileChunk('Foobar'*4000)
    >>> file.data = fc
    >>> file.getSize()
    24000
    >>> file.data == 'Foobar'*4000
    True

    Insert data from file object:

    >>> import StringIO
    >>> sio = StringIO.StringIO()
    >>> sio.write('Foobar'*100000)
    >>> sio.seek(0)
    >>> file.data = sio
    >>> file.getSize()
    600000
    >>> file.data == 'Foobar'*100000
    True


    Last, but not least, verify the interface:

    >>> from zope.interface.verify import verifyClass
    >>> INamedFile.implementedBy(NamedFile)
    True
    >>> verifyClass(INamedFile, NamedFile)
    True
    """

    filename = FieldProperty(INamedFile['filename'])

    def __init__(self, data=b'', contentType='', filename=None):
        if      filename is not None  \
            and contentType in ('', 'application/octet-stream'):
            contentType = get_contenttype(filename=filename)
        self.data = data
        self.filename = filename
        self.contentType = contentType

    def _getData(self):
        if isinstance(self._data, FILECHUNK_CLASSES):
            return six.binary_type(self._data)
        else:
            return self._data

    def _setData(self, data):

        # Handle case when data is a string
        if isinstance(data, six.text_type):
            data = data.encode('utf-8')

        if isinstance(data, six.binary_type):
            self._data, self._size = FileChunk(data), len(data)
            return

        # Handle case when data is None
        if data is None:
            raise TypeError('Cannot set None data on a file.')

        # Handle case when data is already a FileChunk
        if isinstance(data, FILECHUNK_CLASSES):
            size = len(data)
            self._data, self._size = data, size
            return

        # Handle case when data is a file object
        seek = data.seek
        read = data.read

        seek(0, 2)
        size = end = data.tell()

        if size <= 2 * MAXCHUNKSIZE:
            seek(0)
            if size < MAXCHUNKSIZE:
                self._data, self._size = read(size), size
                return
            self._data, self._size = FileChunk(read(size)), size
            return

        # Make sure we have an _p_jar, even if we are a new object, by
        # doing a sub-transaction commit.
        transaction.savepoint(optimistic=True)

        jar = self._p_jar

        if jar is None:
            # Ugh
            seek(0)
            self._data, self._size = FileChunk(read(size)), size
            return

        # Now we're going to build a linked list from back
        # to front to minimize the number of database updates
        # and to allow us to get things out of memory as soon as
        # possible.
        next_ = None
        while end > 0:
            pos = end - MAXCHUNKSIZE
            if pos < MAXCHUNKSIZE:
                pos = 0  # we always want at least MAXCHUNKSIZE bytes
            seek(pos)
            data = FileChunk(read(end - pos))

            # Woooop Woooop Woooop! This is a trick.
            # We stuff the data directly into our jar to reduce the
            # number of updates necessary.
            jar.add(data)

            # This is needed and has side benefit of getting
            # the thing registered:
            data.next = next_

            # Now make it get saved in a sub-transaction!
            transaction.savepoint(optimistic=True)

            # Now make it a ghost to free the memory.  We
            # don't need it anymore!
            data._p_changed = None

            next_ = data
            end = pos

        self._data, self._size = next_, size
        return

    def getSize(self):
        '''
        See `IFile`
        '''
        return self._size

    # See IFile.
    data = property(_getData, _setData)


@implementer(INamedImage)
class NamedImage(NamedFile):
    """
    An non-BLOB image with a filename
    """
    filename = FieldProperty(INamedFile['filename'])

    def __init__(self, data=b'', contentType=b'', filename=None):
        self.contentType, self._width, self._height = getImageInfo(data)
        self.filename = filename
        self._setData(data)

        # Allow override of the image sniffer
        if contentType:
            self.contentType = contentType

        exif_data = get_exif(data)
        if exif_data is not None:
            logger.debug('Image contains Exif Informations. '
                         'Test for Image Orientation and Rotate if necessary.'
                         'Exif Data: %s', exif_data)
            orientation = exif_data['0th'].get(piexif.ImageIFD.Orientation, 1)
            if 1 < orientation <= 8:
                values = rotate_image(self.data)
                self.data, self._width, self._height, self.exif = values
            self.exif_data = exif_data

    def _setData(self, data):
        super(NamedImage, self)._setData(data)
        contentType, self._width, self._height = getImageInfo(self._data)
        if contentType:
            self.contentType = contentType

    def getImageSize(self):
        '''
        See interface `IImage`
        '''
        return (self._width, self._height)

    data = property(NamedFile._getData, _setData)


@implementer(INamedBlobFile)
class NamedBlobFile(Persistent):
    """
    A file stored in a ZODB BLOB, with a filename
    """

    filename = FieldProperty(INamedFile['filename'])

    def __init__(self, data=b'', contentType=b'', filename=None):
        if      filename is not None \
            and contentType in ('', 'application/octet-stream'):
            contentType = get_contenttype(filename=filename)
        self.contentType = contentType
        self._blob = Blob()
        f = self._blob.open('w')
        f.write(b'')
        f.close()
        self._setData(data)
        self.filename = filename

    def open(self, mode='r'):
        if mode != 'r' and 'size' in self.__dict__:
            del self.__dict__['size']
        return self._blob.open(mode)

    def openDetached(self):
        return open(self._blob.committed(), 'rb')

    def _setData(self, data):
        if 'size' in self.__dict__:
            del self.__dict__['size']
        # Search for a storable that is able to store the data
        dottedName = '.'.join((data.__class__.__module__,
                               data.__class__.__name__))
        logger.debug('Storage selected for data: %s', dottedName)
        storable = getUtility(IStorage, name=dottedName)
        storable.store(data, self._blob)

    def _getData(self):
        fp = self._blob.open('r')
        data = fp.read()
        fp.close()
        return data

    _data = property(_getData, _setData)
    data = property(_getData, _setData)

    @property
    def size(self):
        if 'size' in self.__dict__:
            return self.__dict__['size']
        reader = self._blob.open()
        reader.seek(0, 2)
        size = int(reader.tell())
        reader.close()
        self.__dict__['size'] = size
        return size

    def getSize(self):
        return self.size


@implementer(INamedBlobImage)
class NamedBlobImage(NamedBlobFile):
    """
    An image stored in a ZODB BLOB with a filename
    """

    def __init__(self, data=b'', contentType=b'', filename=None):
        super(NamedBlobImage, self).__init__(data, contentType, filename)
        # Allow override of the image sniffer
        if contentType:
            self.contentType = contentType

        exif_data = get_exif(self.data)
        if exif_data is not None:
            logger.debug('Image contains Exif Informations. '
                         'Test for Image Orientation and Rotate if necessary.'
                         'Exif Data: %s', exif_data)
            orientation = exif_data['0th'].get(piexif.ImageIFD.Orientation, 1)
            if 1 < orientation <= 8:
                values = rotate_image(self.data)
                self.data, self._width, self._height, self.exif = values
            else:
                self.exif = exif_data

    def _setData(self, data):
        super(NamedBlobImage, self)._setData(data)
        firstbytes = self.getFirstBytes()
        res = getImageInfo(firstbytes)
        if res == ('image/jpeg', -1, -1) or res == ('image/tiff', -1, -1):
            # header was longer than firstbytes
            start = len(firstbytes)
            length = max(0, MAX_INFO_BYTES - start)
            firstbytes += self.getFirstBytes(start, length)
            res = getImageInfo(firstbytes)
        contentType, self._width, self._height = res
        if contentType:
            self.contentType = contentType

    data = property(NamedBlobFile._getData, _setData)

    def getFirstBytes(self, start=0, length=IMAGE_INFO_BYTES):
        """
        Returns the first bytes of the file.

        Returns an amount which is sufficient to determine the image type.
        """
        fp = self.open('r')
        fp.seek(start)
        firstbytes = fp.read(length)
        fp.close()
        return firstbytes

    def getImageSize(self):
        """
        See interface `IImage`
        """
        if (self._width, self._height) != (-1, -1):
            return (self._width, self._height)
        _, self._width, self._height = getImageInfo(self.data)
        return (self._width, self._height)
