# coding=utf-8
""""""
from __future__ import absolute_import, print_function, unicode_literals

from openpyxl.cell.cell import STRING_TYPES
from six import text_type

from .base import Column

__all__ = ("VocabularyColumn",)


class VocabularyColumn(Column):
    """Columns for :class:`abilian.services.models.BaseVocabulary` items."""

    expected_cell_types = STRING_TYPES

    def data(self, item):
        value = getattr(item, self.attr, None)
        import_value = text_type(value) if value is not None else ""
        yield import_value, value

    def deserialize(self, value):
        # type_ has already 'deserialized' value
        return value
