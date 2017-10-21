#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import struct
from io import BytesIO

logger = __import__('logging').getLogger(__name__)


def process_tiff(data):
    content_type = None
    width = height = -1
    # Standard TIFF, big- or little-endian
    # BigTIFF and other different but TIFF-like formats are not
    # supported currently
    byte_order = data[:2]
    bo_char = ">" if byte_order == "MM" else "<"
    # maps TIFF type id to size (in bytes)
    # and python format char for struct
    tiff_types = {
        1: (1, bo_char + "B"),  # BYTE
        2: (1, bo_char + "c"),  # ASCII
        3: (2, bo_char + "H"),  # SHORT
        4: (4, bo_char + "L"),  # LONG
        5: (8, bo_char + "LL"),  # RATIONAL
        6: (1, bo_char + "b"),  # SBYTE
        7: (1, bo_char + "c"),  # UNDEFINED
        8: (2, bo_char + "h"),  # SSHORT
        9: (4, bo_char + "l"),  # SLONG
        10: (8, bo_char + "ll"),  # SRATIONAL
        11: (4, bo_char + "f"),  # FLOAT
        12: (8, bo_char + "d")   # DOUBLE
    }
    tiff = BytesIO(data)
    ifd_offset = struct.unpack(bo_char + "L", data[4:8])[0]
    try:
        count_size = 2
        tiff.seek(ifd_offset)
        ec = tiff.read(count_size)
        ifd_entry_count = struct.unpack(bo_char + "H", ec)[0]
        # 2 bytes: TagId + 2 bytes: type + 4 bytes: count of values + 4
        # bytes: value offset
        ifd_entry_size = 12
        for i in range(ifd_entry_count):
            entry_offset = ifd_offset + count_size + i * ifd_entry_size
            tiff.seek(entry_offset)
            tag = tiff.read(2)
            tag = struct.unpack(bo_char + "H", tag)[0]
            if tag in (256, 257):
                # if type indicates that value fits into 4 bytes, value
                # offset is not an offset but value itself
                type_ = tiff.read(2)
                type_ = _tiff_type(bo_char, type_)
                if type_ not in tiff_types:
                    raise Exception("Unkown TIFF field type:" +
                                    str(type_))
                type_size = tiff_types[type_][0]
                type_char = tiff_types[type_][1]
                tiff.seek(entry_offset + 8)
                value = tiff.read(type_size)
                value = int(struct.unpack(type_char, value)[0])
                if tag == 256:
                    width = value
                else:
                    height = value
            if width > -1 and height > -1:
                content_type = 'image/tiff'
                break
    except Exception as e:
        logger.error("Unknown image format. %s", e)
    # return
    return content_type, width, height


def _tiff_type(bo_char, type_):
    return struct.unpack(bo_char + "H", type_)[0]
