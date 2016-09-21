# coding=utf-8
"""
"""
from __future__ import absolute_import

from openpyxl.cell.cell import STRING_TYPES

from .base import Column

__all__ = ('VocabularyColumn',)


class VocabularyColumn(Column):
    """
    Columns for :class:`abilian.services.models.BaseVocabulary` items
    """
    expected_cell_types = STRING_TYPES

    def data(self, item):
        value = getattr(item, self.attr, None)
        import_value = unicode(value) if value is not None else u''
        yield import_value, value

    def deserialize(self, value):
        # type_ has already 'deserialized' value
        return value
