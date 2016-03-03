# coding=utf-8
"""
"""
from __future__ import absolute_import


class ExcelError(Exception):
    pass


class ExcelImportError(ExcelError, ValueError):

    def __init__(self, message, imported_value, *args):
        ValueError.__init__(self, message, *args)
        self.imported_value = imported_value
