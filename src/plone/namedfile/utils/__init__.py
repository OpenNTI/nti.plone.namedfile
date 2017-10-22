#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six
import struct
import mimetypes
from io import BytesIO

import piexif

from PIL import Image

from plone.namedfile.utils.png_utils import process_png
from plone.namedfile.utils.jpeg_utils import process_jpeg
from plone.namedfile.utils.tiff_utils import process_tiff

logger = __import__('logging').getLogger(__name__)


def safe_basename(filename):
    """
    Get the basename of the given filename, regardless of which platform
    (Windows or Unix) it originated from.
    """
    fslice = max(
        filename.rfind('/'),
        filename.rfind('\\'),
        filename.rfind(':'),
    ) + 1
    return filename[fslice:]


def get_contenttype(source=None,
                    filename=None,
                    default='application/octet-stream'):
    """
    Get the MIME content type of the given file and/or filename.
    """
    file_type = getattr(source, 'contentType', None)
    if file_type:
        return file_type
    filename = getattr(source, 'filename', filename)
    if filename:
        return mimetypes.guess_type(filename, strict=True)[0] or 'application/octet-stream'
    return default


def bytes_(s, encoding='utf-8', errors='strict'):
    """
    If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``
    """
    if not isinstance(s, bytes):
        if hasattr(s, 'encode'):
            s = s.encode(encoding, errors)
        elif hasattr(s, '__bytes__'):
            s = s.__bytes__()
    return s


def ensure_data(image):
    data = None
    if getattr(image, 'read', None):
        data = image.read()
        image.seek(0)
    else:
        data = image
    return bytes_(data)
_ensure_data = ensure_data


def getImageInfo(data):
    content_type = None
    width, height = -1, -1
    data = ensure_data(data)
    size = len(data)
    # handle GIFs
    if size >= 10 and data[:6] in (b'GIF87a', b'GIF89a'):
        content_type = 'image/gif'
        w, h = struct.unpack(b'<HH', data[6:10])
        width = int(w)
        height = int(h)
    # handle PNG
    elif data[:8] == b'\211PNG\r\n\032\n':
        content_type, width, height = process_png(data)
    # handle JPEGs
    elif data[:2] == b'\377\330':
        content_type, width, height = process_jpeg(data)
    # handle BMPs
    elif size >= 30 and data.startswith(b'BM'):
        kind = struct.unpack(b'<H', data[14:16])[0]
        if kind == 40:  # Windows 3.x bitmap
            content_type = 'image/x-ms-bmp'
            width, height = struct.unpack(b'<LL', data[18:26])
    elif size >= 8 and data[:4] in (b"II\052\000", b"MM\000\052"):
        content_type, width, height = process_tiff(data)
    # Use PIL / Pillow to determ Image Information
    elif data:
        try:
            img = Image.open(BytesIO(data))
            width, height = img.size
            content_type = img.format or ''
            if content_type.lower() == 'tiff':
                content_type = 'image/tiff'
        except Exception as e:
            logger.exception(e)
    # return
    logger.debug('Image Info (Type: %s, Width: %s, Height: %s)',
                 content_type, width, height)
    # Type must be str
    content_type = str(content_type) if content_type else ''
    return content_type, width, height


def get_exif(image):
    exif_data = None
    image_data = ensure_data(image)
    content_type, width, height = getImageInfo(image_data)
    if content_type in ('image/jpeg', 'image/tiff'):
        # Only this two Image Types could have Exif informations
        # see http://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf
        try:
            exif_data = piexif.load(image_data)
        except Exception as e:
            # TODO: determine wich error really happens
            # Should happen if data is to short --> first_bytes
            logger.warn(e)
            exif_data = exif_data = {
                '0th': {
                    piexif.ImageIFD.XResolution: (width, 1),
                    piexif.ImageIFD.YResolution: (height, 1),
                }
            }
    return exif_data


def rotate_image(image_data, method=None):
    """
    Rotate Image if it has Exif Orientation Informations other than 1.

    Do not use PIL.Image.rotate function as this did not transpose the image,
    rotate keeps the image width and height and rotates the image around a
    central point. PIL.Image.transpose also changes Image Orientation.
    """
    orientation = 1  # if not set assume correct orrinetation --> 1
    data = _ensure_data(image_data)
    img = Image.open(BytesIO(data))

    exif_data = None
    if 'exif' in img.info:
        try:
            exif_data = piexif.load(img.info['exif'])
        except (ValueError):
            logger.warn('Exif information currupt')

        if exif_data and piexif.ImageIFD.Orientation in exif_data['0th']:
            orientation = exif_data['0th'][piexif.ImageIFD.Orientation]
        if exif_data \
            and (not exif_data['0th'].get(piexif.ImageIFD.XResolution) or
                 not exif_data['0th'].get(piexif.ImageIFD.YResolution)):
            exif_data['0th'][piexif.ImageIFD.XResolution] = (img.width, 1)
            exif_data['0th'][piexif.ImageIFD.YResolution] = (img.height, 1)
    if exif_data is None:
        width, height = img.size
        exif_data = {
            '0th': {
                piexif.ImageIFD.XResolution: (width, 1),
                piexif.ImageIFD.YResolution: (height, 1),
            }
        }

    if method is not None:
        orientation = method

    logger.debug('Rotate image with input orientation: %s', orientation)

    fmt = img.format
    if orientation == 1:  # not transform necessary
        # img = img
        pass
    elif orientation == 2:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 3:
        img = img.transpose(Image.ROTATE_180)
    elif orientation == 4:
        img = img.transpose(Image.ROTATE_180).transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 5:
        img = img.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 6:
        img = img.transpose(Image.ROTATE_270)
    elif orientation == 7:
        img = img.transpose(Image.ROTATE_90).transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 8:
        img = img.transpose(Image.ROTATE_90)

    if orientation in [5, 6, 7, 8]:
        if      exif_data['0th'][piexif.ImageIFD.XResolution] \
            and exif_data['0th'][piexif.ImageIFD.YResolution]:
            exif_data['0th'][piexif.ImageIFD.XResolution], \
            exif_data['0th'][piexif.ImageIFD.YResolution] = \
                exif_data['0th'][piexif.ImageIFD.YResolution], \
                exif_data['0th'][piexif.ImageIFD.XResolution]
        else:
            exif_data['0th'][piexif.ImageIFD.XResolution], \
            exif_data['0th'][piexif.ImageIFD.YResolution] = \
                (img.width, 1), (img.height, 1)

    # set orientation to normal
    exif_data['0th'][piexif.ImageIFD.Orientation] = 1
    try:
        exif_bytes = piexif.dump(exif_data)
    except Exception as e:
        logger.warn(e)
        del exif_data['Exif'][piexif.ExifIFD.SceneType]
        # This Element piexif.ExifIFD.SceneType cause error on dump
        exif_bytes = piexif.dump(exif_data)
    output_image_data = BytesIO()
    img.save(output_image_data, format=fmt, exif=exif_bytes)
    width, height = img.size
    return output_image_data.getvalue(), width, height, exif_data
