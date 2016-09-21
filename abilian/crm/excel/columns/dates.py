# coding=utf-8
"""
"""
from __future__ import absolute_import

import datetime

from openpyxl.cell.cell import NUMERIC_TYPES, STRING_TYPES, TIME_TYPES
from openpyxl.utils.datetime import from_excel

from .base import Column

__all__ = ('DateTimeColumn', 'DateColumn')


class DateTimeColumn(Column):
    """Column for datetime.datetime objects."""
    _date_fmt = '%Y-%m-%d %H:%M:%S'
    expected_cell_types = TIME_TYPES
    adapt_cell_types = TIME_TYPES + NUMERIC_TYPES
    _text_adapt = '%H:%M:%S %d/%m/%Y'

    # def serialize(self, value):
    #   return value.strftime(self._date_fmt)

    def _adapt_from_cell(self, value, workbook):
        if isinstance(value, STRING_TYPES):
            return datetime.datetime.strptime(value, self._text_adapt)

        if type(value) in NUMERIC_TYPES:
            max_year = datetime.datetime.now().year + 1
            if 2000 < value < max_year:
                # just current year
                return datetime.datetime(int(value), 1, 1)

            # default: cell is formatted as number in excel, but should be displayed
            # as date
            return from_excel(value)

        # just in case we reach here
        return value

    def deserialize(self, value):
        return datetime.datetime.strptime(value, self._date_fmt)


class DateColumn(DateTimeColumn):
    """Column for datetime.date objects."""
    _date_fmt = '%Y-%m-%d'
    _text_adapt = '%d/%m/%Y'

    def _adapt_from_cell(self, value, workbook):
        dt = DateTimeColumn._adapt_from_cell(self, value, workbook)
        return dt.date()

    def deserialize(self, value):
        return DateTimeColumn.deserialize(self, value).date()
