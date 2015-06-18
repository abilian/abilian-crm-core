# coding=utf-8
"""
"""
from __future__ import absolute_import

from .base import ColumnSet


class RelatedColumnSet(ColumnSet):
  """
  ColumnSet for a related entity
  """
  def __init__(self, related_attr, attrs, label=None, required=False):
    """
    :param related_attr: attribute name on main entity that connects to related
    one.

    :param attrs: iterable of `tuple(attribute, label, types map, col_attr)`
    """
    self.related_attr = related_attr
    if label is None:
      label = related_attr.replace(u'_', u' ')
    self.label = self.related_label = label
    self.required = required
    ColumnSet.__init__(self, *attrs)

  def __repr__(self):
    return (
      u'{module}.{cls}(related_attr={attr}, label={label}, '
      u'required={required:}) at 0x{id:x}'
      u''.format(module=self.__class__.__module__,
                 cls=self.__class__.__name__,
                 attr=repr(self.related_attr), label=repr(self.related_label),
                 required=repr(self.required),
                 id=id(self)
      )
    ).encode('utf-8')

  @property
  def attrs(self):
    for attr in ColumnSet.attrs.fget(self):
      yield u'{}.{}'.format(self.related_attr, attr)

  @property
  def labels(self):
    for label in ColumnSet.labels.fget(self):
      if not self.related_label:
        yield label
      else:
        yield u'{}: {}'.format(self.related_label, label)

  def data(self, item):
    # if item is None we must nonetheless call data() for all columns and
    # sub-relatedset columns, so that output values are consistent with columns
    # labels
    related = None
    if item is not None:
      related = getattr(item, self.related_attr)

    return ColumnSet.data(self, related)

  def data_for_import(self, item):
    related = getattr(item, self.related_attr)
    return related, related


class ManyRelatedColumnSet(ColumnSet):
  def __init__(self, related_attr, attrs, label=None, model_cls=None,
               form_cls=None, export_label=None, id_by_name_col=None,
               manager_cls=None):
    """
    :param related_attr: attribute name on main entity that connects to related
    ones

    :param attrs: iterable of tuple (attribute, label, types map)
    """
    from abilian.crm.excel import ExcelManager
    
    self.ID_BY_NAME_COL = id_by_name_col
    self.related_attr = related_attr
    if label is None:
      label = related_attr.replace(u'_', u' ')
    self.related_label = label
    self.model_cls = model_cls
    self.form_cls = form_cls
    self.manager_cls = manager_cls if manager_cls is not None else ExcelManager

    if export_label is None:
      export_label = label
    self.export_label = export_label

    ColumnSet.__init__(self, *attrs)

  def create_manager(self):
    return self.manager_cls(self.model_cls, self.form_cls, ())

  def iter_items(self, obj):
    for item in getattr(obj, self.related_attr):
      yield item

  @property
  def labels(self):
    for label in ColumnSet.labels.fget(self):
      if not self.related_label:
        yield label
      else:
        yield u'{}: {}'.format(self.related_label, label)
