#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import struct

logger = __import__('logging').getLogger(__name__)


def process_png(data):
    size = len(data)
    content_type, width, height = None, -1, -1
    # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
    # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
    # and finally the 4-byte width, height
    if      size >= 24 \
        and data.startswith(b'\211PNG\r\n\032\n') \
        and data[12:16] == b'IHDR':
        content_type = 'image/png'
        width, height = struct.unpack(b'>LL', data[16:24])
        width = int(width)
        height = int(height)
    # Maybe this is for an older PNG version.
    elif size >= 16 and data.startswith(b'\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        content_type = 'image/png'
        width, height = struct.unpack(b'>LL', data[8:16])
        width = int(width)
        height = int(height)
    # return
    return content_type, width, height
