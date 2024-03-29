#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copy hook for proper copying blob data

This file was borrowed from z3c.blobfile and is licensed under the terms of
the ZPL.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import shutil

from ZODB.blob import Blob

from zope.component import adapter

from zope.copy.interfaces import ICopyHook
from zope.copy.interfaces import ResumeCopy

from zope.interface import implementer

from plone.namedfile.interfaces import INamedBlobFile


@implementer(ICopyHook)
@adapter(INamedBlobFile)
class BlobFileCopyHook(object):
    """
    A copy hook that fixes the blob after copying
    """

    def __init__(self, context):
        self.context = context

    def __call__(self, unused_toplevel, register):
        register(self._copyBlob)
        raise ResumeCopy

    def _copyBlob(self, translate):
        # pylint: disable=W0212
        target = translate(self.context)
        target._blob = Blob()
        fsrc = self.context._blob.open('r')
        fdst = target._blob.open('w')
        shutil.copyfileobj(fsrc, fdst)
        fdst.close()
        fsrc.close()
