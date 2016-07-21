# coding=utf-8
"""
"""
from __future__ import absolute_import

from operator import attrgetter

from .base import ColumnSet


class RelatedColumnSet(ColumnSet):
    """ ColumnSet for a related entity. """

    def __init__(self, related_attr, attrs, label=None, required=False):
        """
        :param related_attr: attribute name on main entity that connects to related
        one.

        :param attrs: iterable of :class:`Column` or :class:`ColumnSet` or
                      `tuple(attribute, label, types map, col_attr)`.
        """
        self.related_attr = related_attr
        self.get_related = attrgetter(self.related_attr)

        if label is None:
            label = unicode(related_attr) \
                .replace(u'_', u' ') \
                .replace(u'.', u' ')

        self.label = self.related_label = label
        self.required = required
        ColumnSet.__init__(self, *attrs)

    def __repr__(self):
        return (u'{module}.{cls}(related_attr={attr}, label={label}, '
                u'required={required:}) at 0x{id:x}'
                u''.format(
                    module=self.__class__.__module__,
                    cls=self.__class__.__name__,
                    attr=repr(self.related_attr),
                    label=repr(self.related_label),
                    required=repr(self.required),
                    id=id(self))).encode('utf-8')

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
                yield u'{}:\n {}'.format(self.related_label, label)

    def data(self, item):
        # if item is None we must nonetheless call data() for all columns and
        # sub-relatedset columns, so that output values are consistent with columns
        # labels
        related = None
        if item is not None:
            try:
                related = self.get_related(item)
            except AttributeError:
                pass

        return ColumnSet.data(self, related)

    def data_for_import(self, item):
        related = None
        try:
            related = self.get_related(item)
        except AttributeError:
            pass

        return related, related


class ManyRelatedColumnSet(ColumnSet):

    def __init__(self,
                 related_attr,
                 attrs=None,
                 label=None,
                 model_cls=None,
                 form_cls=None,
                 export_label=None,
                 id_by_name_col=None,
                 manager_cls=None):
        """
        :param related_attr: attribute name on main entity that connects to related
        ones

        :param attrs: iterable of :class:`Column` or :class:`ColumnSet` or tuple
                      (attribute, label, types map).
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

        if attrs is None:
            manager = self.create_manager()
            attrs = manager.columns.columns

        ColumnSet.__init__(self, *attrs)

    def create_manager(self):
        return self.manager_cls(self.model_cls, self.form_cls, ())

    def iter_items(self, obj):
        path = self.related_attr.split('.')

        def iter_obj(obj, attrs):
            if not attrs:
                yield obj
                raise StopIteration

            objs = getattr(obj, attrs[0])
            if not isinstance(objs, (set, list, tuple)):
                objs = (objs,)

            attrs = attrs[1:]
            for item in objs:
                # python 2.7 doesn't have "yield from"...
                for yielded_item in iter_obj(item, attrs):
                    yield yielded_item

        for item in iter_obj(obj, path):
            yield item

    @property
    def labels(self):
        for label in ColumnSet.labels.fget(self):
            if not self.related_label:
                yield label
            else:
                yield u'{}:\n {}'.format(self.related_label, label)
