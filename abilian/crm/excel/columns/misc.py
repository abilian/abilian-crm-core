# coding=utf-8
"""
"""
from __future__ import absolute_import

from openpyxl.cell import STRING_TYPES, NUMERIC_TYPES

from .base import Column


__all__ = ['TextIntegerColumn']


class TextIntegerColumn(Column):
  """
  Column for text that may be entered as integer, like a zipcode.
  """
  expected_cell_types = STRING_TYPES
  adapt_cell_types = NUMERIC_TYPES

  def _adapt_from_cell(self, value, cell_type, workbook):
    if isinstance(value, float):
      value = unicode(int(value))
    return value, value
