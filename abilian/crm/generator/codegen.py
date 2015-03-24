# coding=utf-8
"""
"""
from __future__ import absolute_import

import logging
from collections import OrderedDict
import yaml
import re

import sqlalchemy as sa
import wtforms.fields

from abilian.core.util import slugify
from abilian.services.vocabularies import Vocabulary, get_vocabulary
from abilian.web.forms import widgets as abilian_widgets
from abilian.web.forms.validators import required, optional
from abilian.web.forms.filters import strip
import abilian.web.forms.fields as awbff

from .definitions import (
    COLUMN_TYPES,
    FORM_FILTERS,
    LIST_GENERATORS,
    MAX_IDENTIFIER_LENGTH,
    VALIDATORS,
    WIDGETS,    
)

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
        if hasattr(module, generated_name):
          continue

        name = definition['name'].encode('ascii').strip()
        group = definition.get('group', u'').strip() or None
        label = definition['label'].strip()
        voc_cls = get_vocabulary(name, group=group)

        if voc_cls is None:
          voc_cls = Vocabulary(name=name, group=group, label=label)

        definition['cls'] = voc_cls
        setattr(module, generated_name, voc_cls)

  def gen_model(self, module):
    table_args = []
    type_name = self.data['name'] + 'Base'
    type_bases = (object,)
    attributes = OrderedDict()

    for d in self.data['fields']:
      if 'ignore' in d:
        continue
      is_relationship = False
      attr_name = d['name']
      attr_descr = d['description']
      attr_type = d['type']
      attr_type_options = d.get('type_options', dict())
      extra_args = {}

      if attr_type == 'Entity':
        # Currently taken care of manually
        continue

      if attr_type == 'pass':
        # explicit manual handling - only declared in form groups
        continue

      if attr_type == 'PositiveInteger':
        attr_type = 'Integer'
        table_args.append(
            sa.schema.CheckConstraint(
                attr_name >= 0,
                name='check_{name}_positive'.format(name=attr_name))
        )
      elif attr_type == 'Vocabulary':
        attr_type = 'Integer'
        voc_cls = d['vocabulary']['cls']
        relation_name = attr_name
        attr_name += '_id'
        relation_target = voc_cls
        relation_target_col = voc_cls.id
        is_relationship = True

        if d.get('multiple', False):
          relation_secondary_tbl_name = \
              '{}_{}'.format(self.data['name'].lower(),
                             d['vocabulary']['generated_name'].lower())

      assert_ascii(attr_name)
      if attr_type not in COLUMN_TYPES:
        raise ValueError('Invalid column type: {}'.format(repr(attr_type)))

      attr_type = COLUMN_TYPES[attr_type]
      col_name = attr_name[:MAX_IDENTIFIER_LENGTH]
      extra_args['nullable'] = 'required' not in d

      # Extra dict passed to SQLAlchemy models, and used later by the framework.
      extra_args['info'] = info = {}
      info['label'] = attr_descr
      if 'indexed' in d:
        info['searchable'] = True
        info['index_to'] = ('text',)

      if 'from_list' in d and not is_relationship:
        info['choices'] = OrderedDict(d['from_list'])

      if not is_relationship:
        # simple column attribute
        attr = sa.schema.Column(col_name,
                                attr_type(**attr_type_options),
                                **extra_args)
        attributes[attr_name] = attr
      else:
        if not d.get('multiple'):
          def get_column_attr(func_name, col_name, target_col):
            def gen_column(cls):
              return sa.schema.Column(
                  col_name,
                  sa.ForeignKey(target_col, ondelete='SET NULL'),
              )
            gen_column.func_name = func_name
            return gen_column

          attr = get_column_attr(attr_name, col_name, relation_target_col)
          attributes[attr_name] = sa.ext.declarative.declared_attr(attr)

          def get_rel_attr(func_name, target_cls):
            def gen_relationship(cls):
              return sa.orm.relationship(target_cls)

            gen_relationship.func_name = func_name
            return gen_relationship

          rel_attr = get_rel_attr(relation_name, relation_target)
          attributes[relation_name] = sa.ext.declarative.declared_attr(rel_attr)
        else:
          def get_m2m_attr(func_name, target_cls, secondary_tbl_name=None):
            def gen_m2m_relationship(cls):
              src_name = cls.__tablename__
              target_name = target_cls.__tablename__
              tbl_name = secondary_tbl_name
              if tbl_name is None:
                tbl_name = (src_name + '_' + target_name)
              src_col = cls.__name__.lower() + '_id'
              secondary_table = sa.Table(
                  tbl_name,
                  cls.metadata,
                  sa.Column(src_col,
                            sa.ForeignKey(src_name + '.id')),
                  sa.Column('voc_id',
                            sa.ForeignKey(target_name + '.id')),
                  sa.schema.UniqueConstraint(src_col, 'voc_id'),
              )
              return sa.orm.relationship(target_cls, secondary=secondary_table)

            gen_m2m_relationship.func_name = func_name
            return gen_m2m_relationship

          rel_attr = get_m2m_attr(relation_name, relation_target,
                                  relation_secondary_tbl_name)
          attributes[relation_name] = sa.ext.declarative.declared_attr(rel_attr)

    if table_args:
      attributes['__table_args__'] = table_args

    attributes['__module__'] = module.__name__
    cls = type(type_name, type_bases, attributes)
    setattr(module, type_name, cls)
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

      attr_name = d['name']
      attr_descr = d['description']
      attr_type = d['type']

      if 'ignore' not in d:
        group_name = d['group']
        groups.setdefault(group_name, []).append(attr_name)
        if group_name not in group_names:
          group_names.append(group_name)

      field_type = wtforms.fields.TextField
      extra_args = {'filters': [],
                    'validators': [],}

      if attr_type == "UnicodeText":
        extra_args['filters'].append(strip)
      elif attr_type == "Boolean":
        field_type = wtforms.fields.BooleanField
        extra_args['view_widget'] = abilian_widgets.BooleanWidget()
      elif attr_type == "Date":
        field_type = awbff.DateField
      elif attr_type == "Float":
        field_type = wtforms.fields.DecimalField
        extra_args['default'] = 0
      elif attr_type in ("Integer", 'PositiveInteger'):
        field_type = wtforms.fields.IntegerField
        extra_args['default'] = 0
      elif attr_type == "EmailAddress":
        extra_args['view_widget'] = abilian_widgets.EmailWidget()
        extra_args['filters'].append(strip)
      elif attr_type == "URL":
        extra_args['view_widget'] = abilian_widgets.URLWidget()
        extra_args['filters'].append(strip)
      elif attr_type == 'Vocabulary':
        field_type = awbff.QuerySelect2Field
        extra_args['multiple'] = bool(d.get('multiple', False))
        extra_args['allow_blank'] = not bool(d.get('required', False))
        extra_args['get_label'] = 'label'
        extra_args['view_widget'] = abilian_widgets.ListWidget()

        def gen_voc_query(voc_cls):
          def query_voc():
            return voc_cls.query.active().all()

          query_voc.func_name = 'query_vocabulary_{}'.format(voc_cls.Meta.name)
          return query_voc

        voc_cls = d['vocabulary']['cls']
        extra_args['query_factory'] = gen_voc_query(voc_cls)
      elif attr_type == "Entity":
        # Currenty managed manually
        continue
      elif attr_type == 'pass':
        # explicit manual handling - only declared in form groups
        continue

      else:
        # TODO
        extra_args['filters'].append(strip)
        logger.warning("unknown attr type: %s", repr(attr_type))

      assert not '"' in attr_descr

      # validators
      required_validator = (required() if d.get('required', False)
                            else optional())
      extra_args['validators'].append(required_validator)

      if 'validators' in d:
        validators = d['validators']
        if isinstance(validators, basestring):
          validators = [validators]
        validators = [VALIDATORS[v]() for v in validators]
        extra_args['validators'].extend(validators)

      # filters
      if 'filters' in d:
        filters = d['filters']
        if isinstance(filters, basestring):
          filters = [filters]
        filters = [FORM_FILTERS[f] for f in filters]
        extra_args['filters'] = filters

      if not extra_args['filters']:
        del extra_args['filters']

      for widget_arg in ('widget', 'view_widget'):
        if widget_arg not in d:
          continue

        widget = d[widget_arg]
        if widget not in WIDGETS:
          raise ValueError('Invalid {}: {}'.format(widget_arg,
                                                   widget.encode('utf-8')))
        widget = WIDGETS[widget]
        kw = d.get(widget_arg + '_args', dict())
        extra_args[widget_arg] = widget(**kw)

      if 'from_list' in d and attr_type != 'Vocabulary':
        # TODO: manage required / optional
        field_type = awbff.Select2Field
        if d.get("multiple"):
          field_type = awbff.Select2MultipleField
          extra_args['view_widget'] = abilian_widgets.ListWidget()

        options = list(d['from_list'])
        if 'required' in d:
          if options[0][0] == u'':
            options.pop(0)
        elif options[0] != u'':
          options.insert(0, (u'', u''))

        extra_args['choices'] = options

      if 'from_function' in d and field_type is wtforms.fields.TextField:
        # TODO: manage required / optional
        field_type = awbff.Select2Field
        if d.get("multiple"):
          field_type = awbff.Select2MultipleField
        extra_args['choices'] = LIST_GENERATORS[d['from_function']]()

      if 'lines' in d:
        field_type = wtforms.fields.TextAreaField
        extra_args['widget'] = abilian_widgets.TextArea(
            resizeable='vertical',
            rows=d['lines'])

      attributes[attr_name] = field_type(attr_descr, **extra_args)

    attributes['_groups'] = [(name, groups[name]) for name in group_names]
    attributes['__module__'] = module.__name__
    cls = type(type_name, type_bases, attributes)
    setattr(module, type_name, cls)
    return cls
