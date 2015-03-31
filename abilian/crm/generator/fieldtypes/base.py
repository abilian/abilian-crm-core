# coding=utf-8
"""
"""
from __future__ import absolute_import

import re
from collections import OrderedDict

import sqlalchemy as sa
from ..definitions import MAX_IDENTIFIER_LENGTH

_VALID_IDENTIFIER_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*', re.UNICODE)

def assert_valid_identifier(s):
  match = _VALID_IDENTIFIER_RE.match(s)
  if match is None or match.end() != match.endpos:
    raise ValueError('{} is not a valid python identifier'.format(repr(s)))


class Field(object):

  name = None
  label = u''
  sa_type = None

  #: if not `None`, this is used as __fieldtype__()
  __fieldname__ = None

  @classmethod
  def __fieldtype__(cls):
    """
    :return: identifier name for this field type
    """
    return (cls.__fieldname__
            if cls.__fieldname__ is not None
            else cls.__name__)

  def __init__(self, data):
    """
    """
    self.data = data
    self.name = data['name']
    assert_valid_identifier(self.name)
    self.label = data.get('description', u'')
    self.sa_type_options = data.get('type_options', dict())
    self.required = data.get('required', False)
    self.indexed = data.get('indexed', False)
    self.multiple = data.get('multiple', False)

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


class FormField(object):
  pass
