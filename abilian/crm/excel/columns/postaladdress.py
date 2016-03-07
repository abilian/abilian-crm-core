# coding=utf-8
"""
"""
from __future__ import absolute_import

from abilian.crm.forms import PostalAddressForm
from abilian.crm.models import PostalAddress

from .related import RelatedColumnSet


class PostalAddressColumn(RelatedColumnSet):
    """
  Columns for :class:`abilian.crm.models.PostalAddress` items
  """

    def __init__(self, attr, label=None, type_=None, required=False):
        from .. import ExcelManager
        manager = ExcelManager(PostalAddress, PostalAddressForm)
        columns = manager.columns.columns
        super(PostalAddressColumn, self).__init__(attr, columns, label,
                                                  required)
