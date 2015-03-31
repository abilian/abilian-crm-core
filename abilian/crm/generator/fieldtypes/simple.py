# coding=utf-8
"""
"""
from __future__ import absolute_import

import hashlib
import sqlalchemy as sa
from abilian.core.sqlalchemy import JSON, JSONList, JSONDict

from ..definitions import MAX_IDENTIFIER_LENGTH
from .base import Field
from .registry import register_field


@register_field
class Integer(Field):
  sa_type = sa.types.Integer


@register_field
class PositiveInteger(Integer):

  def get_table_args(self, *args, **kwargs):
    col_name = self.name[:MAX_IDENTIFIER_LENGTH]
    name = 'check_{name}_positive'.format(name=col_name)
    if len(name) > MAX_IDENTIFIER_LENGTH:
      digest = hashlib.md5(self.name).digest()
      exceed = len(name) - MAX_IDENTIFIER_LENGTH
      name = self.name[:MAX_IDENTIFIER_LENGTH - exceed - 7]
      name = 'check_{name}_{digest}_positive'.format(name=name,
                                                     digest=digest[:6])

    yield sa.schema.CheckConstraint(sa.sql.text(col_name + ' >= 0'),
                                    name=name)


@register_field
class UnicodeText(Field):
  sa_type = sa.types.UnicodeText


@register_field
class LargeBinary(Field):
  sa_type = sa.types.LargeBinary


@register_field
class Date(Field):
  sa_type = sa.types.Date


@register_field
class Text(Field):
  sa_type = sa.types.Text


@register_field
class Float(Field):
  sa_type = sa.types.Float


@register_field
class Boolean(Field):
  sa_type = sa.types.Boolean


@register_field
class JSON(Field):
  sa_type = JSON


@register_field
class JSONList(Field):
  sa_type = JSONList


@register_field
class JSONDict(Field):
  sa_type = JSONDict


@register_field
class PhoneNumber(UnicodeText):
  pass


@register_field
class EmailAddress(UnicodeText):
  pass


@register_field
class Entity(Field):
  """
  Currently do nothing: must be implemented by subclassing generated model
  """
  def get_model_attributes(self, *args, **kwargs):
    return ()
