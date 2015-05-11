# coding=utf-8
"""
"""
from __future__ import absolute_import

import re
from collections import OrderedDict

import sqlalchemy as sa
import wtforms.fields

import abilian.web.forms.fields as awbff
import abilian.web.forms.widgets as aw_widgets
import abilian.web.forms.validators as aw_validators
from ..definitions import (
  MAX_IDENTIFIER_LENGTH, VALIDATORS, FORM_FILTERS, WIDGETS,
  LIST_GENERATORS,
)
from .registry import Registrable, get_formfield

_VALID_IDENTIFIER_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*', re.UNICODE)

def assert_valid_identifier(s):
  match = _VALID_IDENTIFIER_RE.match(s)
  if match is None or match.end() != match.endpos:
    raise ValueError('{} is not a valid python identifier'.format(repr(s)))


class Field(Registrable):

  name = None
  label = u''

  #: sqlalchemy column type
  sa_type = None

  #: default form field type
  default_ff_type = 'TextField'

  #: set to False is field supports only single values
  allow_multiple = True

  def __init__(self, model, data, generator):
    """
    """
    self.model = model
    self.data = data
    self.generator = generator
    self.name = data['name']
    assert_valid_identifier(self.name)
    self.label = data.get('description', u'')
    self.sa_type_options = data.get('type_options', dict())
    self.required = data.get('required', False)
    self.indexed = data.get('indexed', False)
    self.multiple = data.get('multiple', False)

    if self.multiple and not self.allow_multiple:
      raise ValueError("Field {!r}: {!r} doesn't support multiple values"
                       "".format(self.name, self.__class__.__fieldname__))

    ff_type = self.get_ff_type()
    data['formfield'] = ff_type(model=model, data=data, generator=generator)

  def get_ff_type(self, *args, **kwargs):
    ff_type = self.default_ff_type
    if not isinstance(ff_type, FormField):
      ff_type = get_formfield(ff_type)
    return ff_type

  def get_model_attributes(self, *args, **kwargs):
    """
    Return attributes to be set on generated model.

    :return: iterable of `(name, type)`
    """
    col_name = self.name[:MAX_IDENTIFIER_LENGTH]
    extra_args = {'nullable': not self.required}
    extra_args['info'] = info = {}
    info['label'] = self.label

    if self.indexed:
      info['searchable'] = True
      info['index_to'] = ('text',)

    if 'from_list' in self.data:
      info['choices'] = OrderedDict(self.data['from_list'])

    attr = sa.schema.Column(
      col_name,
      self.sa_type(**self.sa_type_options),
      **extra_args
    )

    return ((self.name, attr),)

  def get_table_args(self, *args, **kwargs):
    """
    Arguments to be added to __table_args__

    :return: iterable
    """
    return ()


  def get_field(self, *args, **kwargs):
    """
    return a tuple (attribute name, `wtforms.fields.Field` instance)
    """
    field_kw = self.get_field_extra_args(self, *args, **kwargs)
    field_type = self.get_field_type()
    field = field_type(self.description, field_kw)
    return self.name, field


class FormField(Registrable):
  #: form field type
  ff_type = wtforms.fields.TextField

  def __init__(self, model, data, generator):
    self.model = model
    self.data = data
    self.generator = generator
    self.name = data['name']
    assert_valid_identifier(self.name)
    self.label = data.get('description', u'')
    self.sa_type_options = data.get('type_options', dict())
    self.required = data.get('required', False)
    self.multiple = data.get('multiple', False)

  def get_form_attributes(self):
    field_type = self.get_type()
    extra_args = self.get_extra_args()
    yield self.name, field_type(label=self.label, **extra_args)

  def get_type(self, *args, **kwargs):
    field_type = self.ff_type

    if 'lines' in self.data:
      field_type = wtforms.fields.TextAreaField

    if 'from_list' in self.data or 'from_function' in self.data:
      field_type = (awbff.Select2Field
                    if not self.multiple
                    else awbff.Select2MultipleField)
    return field_type

  def get_extra_args(self, *args, **kwargs):
    extra_args = {
      'filters': list(self.get_filters()),
      'validators': list(self.get_validators()),
    }

    # extra validators & filters specified in data
    d = self.data

    description = d.get('help', u'').strip()
    if description:
      extra_args['description'] = description

    if 'validators' in d:
      validators = d['validators']
      if isinstance(validators, basestring):
        validators = [validators]
      validators = [VALIDATORS[v]() for v in validators]
      extra_args['validators'].extend(validators)

    if 'filters' in d:
      filters = d['filters']
      if isinstance(filters, basestring):
        filters = [filters]
      filters = [FORM_FILTERS[f] for f in filters]
      extra_args['filters'].extend(filters)

    for key in ('filters', 'validators',):
      if not extra_args[key]:
        del extra_args[key]

    self.setup_widgets(extra_args)
    return extra_args

  def get_filters(self, *args, **kwargs):
    """
    Default filters
    """
    return ()

  def get_validators(self, *args, **kwargs):
    """
    Default validators
    """
    if self.required:
      return (aw_validators.required(),)
    else:
      return (aw_validators.optional(),)

  def setup_widgets(self, extra_args):
    """
    set 'widget' and 'view_widget' in extra_args
    """
    d = self.data

    if 'from_list' in d:
      if self.multiple:
        extra_args['view_widget'] = aw_widgets.ListWidget()

      options = list(d['from_list'])
      if 'required' in d:
        if options[0][0] == u'':
          options.pop(0)
      elif options[0] != u'':
        options.insert(0, (u'', u''))

      extra_args['choices'] = options

    if 'from_function' in d:
      extra_args['choices'] = LIST_GENERATORS[d['from_function']]()

    if 'lines' in d:
      extra_args['widget'] = aw_widgets.TextArea(resizeable='vertical',
                                                 rows=d['lines'])

    for widget_arg in ('widget', 'view_widget'):
      if widget_arg not in d:
        continue

      widget = d[widget_arg]

      if isinstance(widget, (str, unicode)):
        if widget not in WIDGETS:
          raise ValueError('Invalid {}: {}'.format(widget_arg,
                                                   widget.encode('utf-8')))
        widget = WIDGETS[widget]
        kw = d.get(widget_arg + '_args', dict())
        widget = widget(**kw)

      extra_args[widget_arg] = widget
