# coding=utf-8
""""""
from __future__ import absolute_import, print_function, unicode_literals

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from six import text_type

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def sanitize(val):
    if not isinstance(val, text_type):
        return val

    return ILLEGAL_CHARACTERS_RE.sub("", val)
