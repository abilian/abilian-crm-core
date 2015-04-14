# coding=utf-8
"""
"""
from __future__ import absolute_import

import logging
from collections import OrderedDict
import yaml
import re

import sqlalchemy as sa
from abilian.core.entities import Entity
from abilian.core.util import slugify
from abilian.services.vocabularies import Vocabulary, get_vocabulary

from .fieldtypes import get_field
from . import autoname

logger = logging.getLogger(__name__)


def assert_ascii(s):
  try:
    s.encode('ascii')
  except UnicodeError:
    raise ValueError('{} is not an ASCII string'.format(repr(s)))


class CodeGenerator(object):

  def __init__(self, yaml_file):
    self.vocabularies = {}
    self.load_file(yaml_file)

  def load_file(self, yaml_file):
    self.data = yaml.load(yaml_file)

    for d in self.data['fields']:
      vocabulary = d.get('vocabulary', None)
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
      from_list = d.get('from_list', None)
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
    table_args = []
    model_name = self.data['name']
    type_name = model_name + 'Base'
    type_base = Entity
    type_base_attrs = sa.inspect(type_base).attrs
    attributes = OrderedDict()
    attributes['__module__'] = module.__name__
    attributes['__tablename__'] = model_name.lower()

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

      field = FieldCls(model=model_name, data=d)

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


    if table_args:
      attributes['__table_args__'] = tuple(table_args)

    cls = type(type_name, (type_base,), attributes)
    setattr(module, type_name, cls)

    auto_name = unicode(self.data.get('auto_name') or u'').strip()
    if auto_name:
      autoname.setup(cls, auto_name)

    return cls

  def gen_form(self, module):
    type_name = self.data['name'] + 'EditFormBase'
    type_bases = (object,)
    attributes = OrderedDict()

    groups = {}
    group_names = []

    for d in self.data['fields']:
      if 'ignore' in d or 'hidden' in d:
        continue

      if 'ignore' not in d:
        group_name = d['group']
        groups.setdefault(group_name, []).append(d['name'])
        if group_name not in group_names:
          group_names.append(group_name)

      if d['type'] == 'pass':
        # explicit manual handling - only declared in form groups
        continue

      field = d['formfield']
      field_type = field.get_type()
      extra_args = field.get_extra_args()
      attributes[field.name] = field_type(field.label, **extra_args)

    attributes['_groups'] = [(name, groups[name]) for name in group_names]
    attributes['__module__'] = module.__name__
    cls = type(type_name, type_bases, attributes)
    setattr(module, type_name, cls)
    return cls
