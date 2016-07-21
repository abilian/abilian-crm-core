# coding=utf-8
"""
"""
from __future__ import absolute_import

from .related import ManyRelatedColumnSet


class ManyYearlyColumnSet(ManyRelatedColumnSet):

    def __init__(self, related_attr='ignored', *args, **kwargs):
        super(ManyYearlyColumnSet, self).__init__(
            related_attr='__yearly_data__', *args, **kwargs)

    def iter_items(self, obj):
        for data in getattr(obj, self.related_attr).values():
            yield data
