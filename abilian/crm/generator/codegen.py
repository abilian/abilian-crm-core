# coding=utf-8
"""
"""
from __future__ import absolute_import

import logging
import re
from collections import OrderedDict

import sqlalchemy as sa
import yaml

from abilian.core.entities import Entity
from abilian.core.models import attachment, comment, tag
from abilian.core.util import slugify
from abilian.services.security import CREATE, DELETE, READ, WRITE, \
    Permission, Role
from abilian.services.vocabularies import Vocabulary, get_vocabulary
from abilian.web.forms import Form, FormPermissions
from abilian.web.tags.extension import ns as tag_ns

from . import autoname
from .fieldtypes import get_field

logger = logging.getLogger(__name__)


def assert_ascii(s):
    try:
        s.encode('ascii')
    except UnicodeError:
        raise ValueError('{} is not an ASCII string'.format(repr(s)))


class CodeGenerator(object):

    def __init__(self, yaml_file=None, data=None, **options):
        self.vocabularies = {}
        self.options = options
        self._model_finalizers = []
        if data is not None:
            self.data = data
        else:
            self.load_file(yaml_file)
        self.prepare_data()

    def load_file(self, yaml_file):
        self.data = yaml.load(yaml_file)

    def add_model_finalizer(self, finalizer):
        self._model_finalizers.append(finalizer)

    def set_current_module(self, module):
        self.module = module

    def prepare_data(self):
        """Massage data before models creations."""
        for d in self.data['fields']:
            vocabulary = d.get('vocabulary')
            if vocabulary:
                name = u'Vocabulary_'
                group = vocabulary.get('group', u'').strip()
                if group:
                    group = slugify(group, u'_')
                    name += group + u'__'
                name += vocabulary['name']

                if name in self.vocabularies:
                    # already defined in another field, maybe on another model: share
                    # existing definition so that generated class is also accessible
                    d['vocabulary'] = self.vocabularies[name]
                else:
                    vocabulary['generated_name'] = name.encode('ascii')
                    self.vocabularies[name] = vocabulary
                continue

            # slugify list items
            from_list = d.get('from_list')
            if from_list is None:
                continue

            key_val_list = []
            seen = dict()
            for item in from_list:
                k = v = item
                if isinstance(item, (list, tuple)):
                    k, v = item
                    if isinstance(k, str):
                        k = k.decode('utf-8')
                    v = unicode(v)
                else:
                    if not isinstance(item, unicode):
                        item = item.decode('utf-8')
                    k = unicode(slugify(item, u'_'))

                k = re.sub(u'[^\w\s-]', '', k).strip().upper()
                k = re.sub(u'[-\s]+', '_', k)
                #  avoid duplicates: suffix by a number if needed
                current = k
                count = 0
                while k in seen and seen[k] != v:
                    count += 1
                    k = '{}_{}'.format(current, count)

                seen[k] = v
                key_val_list.append((k, v))

            d['from_list'] = key_val_list

    def init_vocabularies(self, module):
        self.set_current_module(module)
        for generated_name, definition in self.vocabularies.items():
            name = definition['name'].encode('ascii').strip()
            group = definition.get('group', u'').strip() or None
            label = definition['label'].strip()
            voc_cls = get_vocabulary(name, group=group)

            if voc_cls is None:
                voc_cls = Vocabulary(name=name, group=group, label=label)

            definition['cls'] = voc_cls

            if not hasattr(module, generated_name):
                setattr(module, generated_name, voc_cls)

    def gen_model(self, module):
        self.set_current_module(module)
        table_args = self.data.get('table_args', [])
        model_name = self.data['name']
        type_name = self.data.get('type_name', model_name + 'Base')
        type_base = self.data.get('type_base', Entity)
        try:
            type_base_attrs = sa.inspect(type_base).attrs
        except sa.exc.NoInspectionAvailable:
            type_base_attrs = frozenset()

        attributes = OrderedDict(self.data.get('attributes', {}))
        attributes['__module__'] = module.__name__
        attributes['__tablename__'] = self.data.get('tablename',
                                                    model_name.lower())

        # default permissions
        permissions = self.data.get('permissions')
        if permissions:
            default_permissions = {}
            for perm, roles in permissions.items():
                perm = perm.strip()
                if not perm:
                    raise TypeError('Found empty string for permission')
                perm = Permission(perm)
                roles = {Role(r.strip()) for r in roles if r.strip()}

                if not roles:
                    continue

                default_permissions[perm] = roles
        else:
            default_permissions = self.options.get('default_permissions', {})

        if default_permissions:
            for p in (WRITE, CREATE, DELETE):
                if p in default_permissions:
                    read_permissions = default_permissions.setdefault(READ,
                                                                      set())
                    read_permissions |= default_permissions[p]

            if WRITE in default_permissions:
                for p in (CREATE, DELETE):
                    if p not in default_permissions:
                        default_permissions[p] = set(default_permissions[WRITE])

            attributes['__default_permissions__'] = default_permissions

        # Fields
        for d in self.data['fields']:
            if 'ignore' in d:
                continue

            type_ = d['type']
            if type_ == 'pass':
                # explicit manual handling - only declared in form groups
                continue

            FieldCls = get_field(type_)
            if FieldCls is None:
                raise ValueError('Unknown type: {}'.format(repr(type_)))

            field = FieldCls(model=model_name, data=d, generator=self)

            if d['name'] in type_base_attrs:
                # existing field (i.e, Entity.name), don't override column else it will
                # be duplicated in joined table, and missing some setup found in
                # overriden column (like indexability)
                #
                # since field has been setup, it has created 'formfield' instance,
                # required for form generation
                continue

            for name, attr in field.get_model_attributes():
                assert name not in attributes
                attributes[name] = attr

            for arg in field.get_table_args():
                table_args.append(arg)

        for finalize in self._model_finalizers:
            finalize(attributes, table_args, module)

        if table_args:
            attributes['__table_args__'] = tuple(table_args)

        cls = type(type_name, (type_base,), attributes)
        self.data['cls'] = cls
        setattr(module, type_name, cls)

        # automatic name from other fields
        auto_name = unicode(self.data.get('auto_name') or u'').strip()

        if auto_name:
            autoname.setup(cls, auto_name)

        # commentable?
        if self.data.get('commentable', False):
            comment.register(cls)

        # attachments support ?
        if self.data.get('attachments', False):
            attachment.register(cls)

        # tagging support ?
        cls_tags_ns = self.data.get('tag')
        if cls_tags_ns:
            tag.register(cls)
            tag_ns(cls_tags_ns)(cls)

        return cls

    def gen_form(self, module):
        self.set_current_module(module)
        type_name = self.data['name'] + 'EditFormBase'
        type_bases = (Form,)
        attributes = OrderedDict()

        groups = {}
        group_names = []
        read_permissions = {}
        write_permissions = {}

        for d in self.data['fields']:
            if 'ignore' in d or 'hidden' in d:
                continue

            field_name = d['name']

            if 'ignore' not in d:
                group_name = d.get('group', 'default group')
                groups.setdefault(group_name, []).append(field_name)
                if group_name not in group_names:
                    group_names.append(group_name)

                perms = d.get('permissions', {})
                write = {Role(r.strip()) for r in perms.get('write', ())}
                read = write | {Role(r.strip()) for r in perms.get('read', ())}
                if write:
                    write_permissions[field_name] = write
                if read:
                    read_permissions[field_name] = read

            if d['type'] == 'pass':
                # explicit manual handling - only declared in form groups
                continue

            field = d['formfield']
            for name, attr in field.get_form_attributes():
                attributes[name] = attr

        attributes['_permissions'] = FormPermissions(
            fields_read=read_permissions,
            fields_write=write_permissions,)
        attributes['_groups'] = OrderedDict((name, groups[name])
                                            for name in group_names)
        attributes['__module__'] = module.__name__
        cls = type(type_name, type_bases, attributes)
        setattr(module, type_name, cls)
        return cls
