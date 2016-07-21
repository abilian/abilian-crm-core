# coding=utf-8
"""
"""
from __future__ import absolute_import

from operator import attrgetter

from markupsafe import Markup
from wtforms.fields import FieldList

from abilian.core.entities import Entity

_NULL_MARK = object()


class Invalid(object):
    """
    Mark invalid values
    """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return u'{module}.{cls}(value={value})'.format(
            module=self.__class__.__module__,
            cls=self.__class__.__name__,
            value=repr(self.value),).encode('utf-8')

    def __unicode__(self):
        return u'Invalid: {}'.format(repr(self.value))

    def __str__(self):
        return unicode(self).encode('utf-8')


class Update(object):
    """
    Holds information about a value update.  Used in import_data()
    """
    error = False
    error_msg = None

    def __init__(self, attr, current, update, value=_NULL_MARK):
        """
        @param current: current value
        @param update: updated value as received in XLS file (Entity key for
        example)
        @param value: value to be set on object (Entity instance for example)
        """
        self.attr = attr
        self.current = current
        self.update = update
        self.value = value if value is not _NULL_MARK else update

    def __nonzero__(self):
        return (self.current != self.value) or self.error

    def _render(self, manager, value):
        form = manager.form
        field = getattr(form, self.attr)
        if isinstance(field, FieldList):
            for v in value:
                field.append_entry(v)
        else:
            field.data = field.object_data = value
        return Markup(field.render_view())

    def render_current(self, manager):
        return self._render(manager, self.current)

    def render_value(self, manager):
        return self._render(manager, self.value)


class Column(object):
    """
    A single column
    """
    # a column may be declared unconditionnaly not importable
    importable = True
    expected_cell_types = None
    adapt_cell_types = ()
    UpdateCls = Update

    def __init__(self, attr, label, type_, required=False, col_attr=None):
        """ type_: callable to convert an imported value to model one.
        """
        self.attr = attr
        self.col_attr = col_attr if col_attr is not None else attr
        self.label = label
        self.type_ = type_
        self.required = required

    def __repr__(self):
        return (
            '{module}.{cls}(attr={attr!r}, label={label!r}, type_={type_!r}, '
            'required={required!r}) at 0x{id:x}'
            ''.format(
                module=self.__class__.__module__,
                cls=self.__class__.__name__,
                attr=self.attr,
                label=self.label,
                type_=self.type_,
                required=self.required,
                id=id(self)))

    def __iter__(self):
        yield self

    iter_flatened = __iter__

    @property
    def attrs(self):
        yield self.col_attr

    @property
    def labels(self):
        yield self.label

    @property
    def colspan(self):
        return 1

    def data(self, item):
        if item is None:
            yield None, None
            raise StopIteration

        def to_str(item):
            if isinstance(item, str):
                return item.decode('utf-8')
            elif isinstance(item, Entity):
                return item.name
            else:
                return unicode(item)

        value = attrgetter(self.attr)(item)
        import_value = item.display_value(self.attr, value=value)
        if isinstance(import_value, Entity):
            import_value = import_value.name
        elif isinstance(import_value, list):
            import_value = u"; ".join((to_str(i) for i in import_value))

        if isinstance(import_value, str):
            import_value = import_value.decode('utf-8')
        if isinstance(import_value, unicode):
            import_value = import_value.strip().replace(u'\r\n', u'\n')

        yield import_value, value

    def data_for_import(self, item):
        # data() returns an iterator of "length" 1, data_for_import must return a
        # value directly
        for data in self.data(item):
            return data

    def adapt_from_cell(self, value, cell_type, workbook):
        if cell_type not in self.adapt_cell_types:
            raise ValueError('Cannot adapt {}'.format(cell_type))
        return self._adapt_from_cell(value, cell_type, workbook)

    def _adapt_from_cell(self, value, cell_type, workbook):
        raise NotImplementedError

    # def serialize(self, value):
    #   return value

    def deserialize(self, value):
        if self.type_ is not None:
            value = self.type_(value)
        return value


class ColumnSet(object):
    """
    A set of columns to be added to current export / import
    """
    # a columnset may be declared unconditionnaly not importable
    importable = True
    expected_cell_types = None
    UpdateCls = Update

    def __init__(self, *columns):
        self.columns = []
        for c in columns:
            if isinstance(c, (tuple, list)):
                c = Column(*c)

            if not isinstance(c, (Column, ColumnSet)) and callable(c):
                c = c()

            assert isinstance(c, (Column, ColumnSet))
            self.columns.append(c)

    def __iter__(self):
        return iter(self.columns)

    def iter_flatened(self):
        for sub_columns in self:
            for c in sub_columns.iter_flatened():
                yield c

    @property
    def colspan(self):
        return sum(c.colspan for c in self.columns)

    @property
    def attrs(self):
        for c in self.columns:
            for attr in c.attrs:
                yield attr

    @property
    def labels(self):
        for c in self.columns:
            for label in c.labels:
                yield label

    def data(self, item):
        for c in self.columns:
            for result in c.data(item):
                yield result

    def data_for_import(self, item):
        """ Like ::meth `data`, but for import. The difference is that it must
        return a tuple like Column.data.

        In the generic context of a ColumnSetit has no sense, but
        a RelatedColumnSet may return the related entity.
        """
        return _NULL_MARK, _NULL_MARK

    def serialize(self, value):
        return value

    def deserialize(self, value):
        return value
