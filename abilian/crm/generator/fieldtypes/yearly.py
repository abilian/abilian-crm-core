# coding=utf-8
"""
Field for yearly data

Use to add attributes values by year; might be several in a row. If model has
other yearly attributes, they will be in the same row (from database POV).

In yml they are specified like this:

::
    - name: attr
      type: Yearly
      type_args:
        fields:
          - name: attr_1
            type: Integer
          - name: ...

"""
from __future__ import absolute_import

from functools import total_ordering
from operator import attrgetter

import sqlalchemy as sa
from sqlalchemy.orm.collections import collection
from wtforms.fields import FieldList, IntegerField
from wtforms.utils import unset_value as unset_value

import abilian.web.forms.fields as awbff
import abilian.web.forms.widgets as aw_widgets
from abilian.core.extensions import db
from abilian.core.models import SYSTEM
from abilian.i18n import _l
from abilian.web.forms import Form

from .base import FormField as FormFieldGeneratorBase
from .base import Field
from .registry import form_field, model_field

_MARK = object()


@total_ordering
class YearlyBase(db.Model):
    """
    Base model for yearly data collections
    """
    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True, info=SYSTEM)
    year = sa.Column(sa.SmallInteger, nullable=False)

    def __eq__(self, other):
        raise NotImplementedError

    def __lt__(self, other):
        raise NotImplementedError


class YearlyCollection(sa.orm.collections.MappedCollection):
    """
    `sa.orm.relationships` collection class for yearly values.

    Years are used as keys.
    """

    def __init__(self, yearly_cls):
        super(YearlyCollection, self).__init__(YearlyCollection._keyfunc)
        self.yearly_cls = yearly_cls

    @collection.internally_instrumented
    def __setitem__(self, key, value, _sa_initiator=None):
        if not isinstance(key, int):
            raise ValueError('Key must be an integer, key={!r}'.format(key))
        value = self._value_fromdict(key, value)
        return super(YearlyCollection, self).__setitem__(key, value,
                                                         _sa_initiator)

    @collection.internally_instrumented
    def setdefault(self, key, default=None):
        """
        D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D.
        """
        if key not in self:
            self.__setitem__(key, default)

        # dont't return default as passed but value as actually set.
        # allow to pass 'default' as dict and get a YearlyBase class in return
        return self.__getitem__(key)

    @collection.converter
    def _convert(self, dictlike):
        for incoming_key, value in sa.orm.util.dictlike_iteritems(dictlike):
            yield self._value_fromdict(incoming_key, value)

    def _value_fromdict(self, key, value):
        if not isinstance(value, YearlyBase):
            if not isinstance(value, dict):
                raise ValueError(
                    'Value must be a YearlyBase based class or a dict')

            value['year'] = key
            value = self.yearly_cls(**value)
        else:
            value_key = self.keyfunc(value)
            if key != value_key:
                raise TypeError(
                    "Found incompatible key {!r} for value {!r}; this collection's "
                    "keying function requires a key of {!r} for this value."
                    "".format(key, value, value_key))

        return value

    def keys(self):
        return sorted(super(YearlyCollection, self).keys())

    def iterkeys(self):
        for key in self.keys():
            yield key

    __iter__ = iterkeys

    def values(self):
        return sorted(
            super(YearlyCollection, self).values(),
            key=YearlyCollection._keyfunc)

    def itervalues(self):
        for v in self.values():
            yield v

    def items(self):
        return [(obj.year, obj) for obj in self.itervalues()]

    def iteritems(self):
        for item in self.items():
            yield item

    def latest(self, attr):
        """
        Return the most recent tuple `(year, value)` for given :attr:
        """
        getter = attrgetter(attr)
        for year, infos in reversed(self.items()):
            val = getter(infos)
            if val is not None:
                return (year, infos)

        return (None, None)

    @staticmethod
    def _keyfunc(obj):
        return obj.year


class YearlyAttrProxy(object):
    """
    Proxy model to allow get and update a particular attribute on yearly
    collections, as if it was directly a model collection.
    """
    __slots__ = ('yearly_data', 'attrs')

    def __init__(self, yearly_data, attrs):
        self.attrs = frozenset(attrs)
        self.yearly_data = yearly_data

    def clear(self):
        for attr in self.attrs:
            setattr(self.yearly_data, attr, None)

    def update(self, value):
        if isinstance(value, YearlyAttrProxy):
            for attr in self.attrs:
                setattr(self, attr, getattr(value, attr))
        elif isinstance(value, dict):
            for attr in self.attrs:
                v = value.get(attr)
                if v is not None:
                    setattr(self, attr, v)
        else:
            raise TypeError(
                'Except a YearlyAttrProxy or dict instance, got: {!r}'
                ''.format(type(value).__name__))

    def __getattr__(self, name):
        if name != 'attrs' and (name == 'year' or name in self.attrs):
            return self.yearly_data.__getattribute__(name)

        raise AttributeError

    def __setattr__(self, name, value):
        if name != 'attrs' and (name == 'year' or name in self.attrs):
            return self.yearly_data.__setattr__(name, value)

        return super(YearlyAttrProxy, self).__setattr__(name, value)

    def __nonzero__(self):
        return any(
            getattr(self.yearly_data, attr, None) is not None
            for attr in self.attrs)

    def __repr__(self):
        return '<{} for {}: {!r}) at 0x{:x}>'.format(
            self.__class__.__name__, self.yearly_data.__class__.__name__,
            tuple(sorted(self.attrs)), id(self))


# proxy sa.inspect()
sa.inspection._inspects(YearlyAttrProxy)(
    lambda target: sa.inspect(target.yearly_data))


class YearlyCollectionProxy(dict):
    """
    Proxy the collection with :class:`YearlyAttrProxy` instances as values.

    New keys insert new :class:`YearlyAttrProxy` instances
    """

    def __init__(self, collection, attrs):
        self.__collection = collection
        self.__attrs = frozenset(attrs)

        for year, year_data in collection.iteritems():
            value = YearlyAttrProxy(year_data, self.__attrs)
            if value:
                self.__setitem__(year, value)

    def __getitem__(self, key):
        if key not in self.__collection:
            if key in self:
                super(YearlyCollectionProxy, self).__delitem__(key)
            raise KeyError

        year_data = self.__collection[key]
        if key not in self:
            super(YearlyCollectionProxy, self).__setitem__(
                key, YearlyAttrProxy(year_data, self.__attrs))

        return super(YearlyCollectionProxy, self).__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(value, YearlyAttrProxy):
            if value.attrs != self.__attrs:
                raise ValueError('Incompatible attribute proxys: {!r}, {!r}'
                                 ''.format(self, value))
            if key not in self and value:
                self[key]  # add key since value is nonzero
                return  # same proxy: no update needed

        elif isinstance(value, dict):
            if set(value) - self.__attrs:
                raise ValueError(
                    'Some keys are invalid for this collection proxy: {!r} (valid: {!r})'
                    ''.format(
                        sorted(set(value) - self.__attrs), sorted(
                            self.__attrs)))
            if key not in self.__collection:
                self.__collection[key] = {}

        proxy = self[key]
        proxy.update(value)

    def __delitem__(self, key):
        value = self.__getitem__(key, None)
        if value is not None:
            value.clear()
            del value
        super(YearlyCollectionProxy, self).__delitem__(key)

    def setdefault(self, key, default=None):
        'D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D'
        if key not in self.__collection:
            self.__setitem__(key, default)

        # dont't return default as passed but value as actually set.
        # allow to pass 'default' as dict and get a YearlyBase class in return
        return self.__getitem__(key)

    def keys(self):
        return sorted(super(YearlyCollectionProxy, self).keys())

    def iterkeys(self):
        for key in self.keys():
            yield key

    __iter__ = iterkeys

    def values(self):
        return sorted(
            super(YearlyCollectionProxy, self).values(),
            key=YearlyCollection._keyfunc)

    def itervalues(self):
        for v in self.values():
            yield v

    def items(self):
        return [(obj.year, obj)
                for obj in sorted(
                    self.itervalues(), key=YearlyCollectionProxy._keyfunc)]

    def iteritems(self):
        for item in self.items():
            yield item


class YearlyAttribute(object):
    """
    An association proxy that allow multiple attributes grouping
    Descriptor for single attribute access
    """
    __slots__ = ('_attrs', '_collection_proxy')

    def __init__(self, attrs):
        self._attrs = frozenset(attrs)

    def __get__(self, instance, owner):
        if instance is None:
            # attribute accessed on class ('owner')
            return self

        return YearlyCollectionProxy(instance.__yearly_data__, self._attrs)

    def __set__(self, instance, value):
        yearly_data = instance.__yearly_data__
        for year, year_data in yearly_data.iteritems():
            if year not in value:
                for attr in self._attrs:
                    setattr(year_data, attr, None)

        for year, values in value.iteritems():
            year_data = yearly_data.setdefault(year, {})
            for attr in self._attrs:
                val = values.get(attr, _MARK)
                if val is not _MARK:
                    setattr(year_data, attr, val)

    def __delete__(self, instance):
        for year, year_data in instance.__yearly_data__.iteritems():
            for attr in self._attrs:
                setattr(year_data, attr, None)

    def __repr__(self):
        return '<{}{!r} at 0x{:x}>'.format(self.__class__.__name__, self._attrs,
                                           id(self))


@model_field
class Yearly(Field):

    default_ff_type = 'YearlyFormField'

    def __init__(self, model, data, generator, *args, **kwargs):
        super(Yearly, self).__init__(model, data, generator, *args, **kwargs)
        self.data['type_args']['name'] = self.name
        generator.add_model_finalizer(self.finalize)

        if 'yearly' not in generator.data:
            model_lower = model.lower()
            related_attr_id = '{}_id'.format(model_lower)
            tablename = '{}_yearly'.format(model_lower)
            type_name = '{}YearlyData'.format(model)
            fk_col = sa.Column(sa.Integer(),
                               sa.ForeignKey(self.model.lower() + '.id'))
            attributes = dict()
            attributes[related_attr_id] = fk_col
            attributes['_' + model_lower] = sa.orm.relationship(
                model,
                primaryjoin=u'{tablename}.c.{related_attr_id} == {remote}.c.id'.
                format(
                    tablename=tablename,
                    related_attr_id=related_attr_id,
                    remote=self.model.lower()))
            attributes['__auditable_entity__'] = ('_' + model_lower,
                                                  '__yearly_data__', ('year',))

            generator.data['yearly'] = dict(
                name=type_name,
                type_name=type_name,
                type_base=YearlyBase,
                tablename=tablename,
                related_attr_id=related_attr_id,
                related_attr=model_lower,
                cls=None,
                table_args=[
                    sa.schema.UniqueConstraint(related_attr_id, 'year')
                ],
                attributes=attributes,
                fields=[])

        self.yearly_data = generator.data['yearly']

    def get_model_attributes(self, *args, **kwargs):
        forbidden_attrs = {'id', 'year'}
        fields = self.data['type_args']['fields']
        if any(f['name'] in forbidden_attrs for f in fields):
            raise ValueError('{} are forbidden field names'.format(','.join(
                sorted(forbidden_attrs))))

        self.yearly_data['fields'].extend(fields)
        yield self.name, YearlyAttribute(f['name'] for f in fields)

    def finalize(self, attributes, table_args, module, *arg, **kwargs):
        """Create related model and relationships.
        """
        if self.yearly_data.get('cls') is None:
            self.create_related_model(module)

        yearly_cls = self.yearly_data['cls']
        primaryjoin = u'{local} == {remote}'.format(
            local=u'{__tablename__}.c.id'.format(**attributes),
            remote=u'{tablename}.c.{related_attr_id}'.format(
                **self.yearly_data),)
        attributes['__yearly_data__'] = sa.orm.relationship(
            yearly_cls,
            primaryjoin=primaryjoin,
            collection_class=lambda: YearlyCollection(yearly_cls),
            cascade='all, delete-orphan',)

    def create_related_model(self, module):
        # cannot import at top of the file
        from ..codegen import CodeGenerator

        generator = CodeGenerator(data=self.yearly_data)
        generator.add_model_finalizer(self.yearly_model_finalizer)
        generator.init_vocabularies(module)
        rel_cls = generator.gen_model(module)
        self.yearly_data['cls'] = rel_cls
        return rel_cls

    def yearly_model_finalizer(self, attributes, *args, **kwargs):
        """Implements total_ordering methods.
        """
        rel_attr_id = self.yearly_data['related_attr_id']
        column_attributes = [
            attr for attr, definition in attributes.iteritems()
            if isinstance(definition, sa.Column)
        ]

        def _eq(self, other):
            return (isinstance(other, self.__class__) and all(
                getattr(self, attr) == getattr(other, attr)
                for attr in column_attributes))

        def _lt(self, other):
            if getattr(self, rel_attr_id, -1) < getattr(other, rel_attr_id, -1):
                # dummy case, comparing objects not related to the same entity instance
                return True
            return self.year < other.year

        attributes['__eq__'] = _eq
        attributes['__lt__'] = _lt


class YearlyFieldList(awbff.ModelFieldList):

    def process(self, formdata, data=unset_value):
        if data is not unset_value and isinstance(data, dict):
            data = data.values()
        return super(YearlyFieldList, self).process(formdata, data)

    def _add_entry(self, formdata=None, data=unset_value, index=None):
        return FieldList._add_entry(
            self, formdata=formdata, data=data, index=index)

    def populate_obj(self, obj, name):
        entities = {}
        for entry in self.entries:
            data = entry.data
            year = data['year']
            entities[year] = data

        setattr(obj, name, entities)


@form_field
class YearlyFormField(FormFieldGeneratorBase):
    ff_type = YearlyFieldList

    def __init__(self, *args, **kwargs):
        super(YearlyFormField, self).__init__(*args, **kwargs)

    def get_extra_args(self, *args, **kwargs):
        from ..codegen import CodeGenerator

        generator = CodeGenerator(data=self.data['type_args'])
        year_field = IntegerField(label=_l(u'Year'))
        FormBase = generator.gen_form(self.generator.module)
        ModelField = type(self.name + 'Form', (
            FormBase,
            Form,), {'year': year_field,})

        extra_args = super(YearlyFormField, self).get_extra_args(*args,
                                                                 **kwargs)
        extra_args['unbound_field'] = awbff.FormField(ModelField, default=dict)
        extra_args['population_strategy'] = 'update'
        extra_args['min_entries'] = 1
        return extra_args

    def setup_widgets(self, extra_args):
        extra_args['widget'] = aw_widgets.TabularFieldListWidget()
        extra_args['view_widget'] = aw_widgets.ModelListWidget()
