# coding=utf-8
"""
"""
from __future__ import absolute_import

import hashlib

import sqlalchemy as sa
import wtforms.fields
from abilian.core.sqlalchemy import JSON, JSONList, JSONDict
import abilian.web.forms.fields as awbff

from ..definitions import MAX_IDENTIFIER_LENGTH
from .base import Field
from .registry import model_field


@model_field
class Integer(Field):
  sa_type = sa.types.Integer
  default_ff_type = 'IntegerField'


@model_field
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


@model_field
class UnicodeText(Field):
  sa_type = sa.types.UnicodeText


@model_field
class LargeBinary(Field):
  sa_type = sa.types.LargeBinary


@model_field
class Date(Field):
  sa_type = sa.types.Date
  default_ff_type = 'DateField'


@model_field
class Text(Field):
  sa_type = sa.types.Text


@model_field
class Float(Field):
  sa_type = sa.types.Float
  default_ff_type = 'DecimalField'


@model_field
class Boolean(Field):
  sa_type = sa.types.Boolean
  default_ff_type = 'BooleanField'


@model_field
class JSON(Field):
  sa_type = JSON


@model_field
class JSONList(Field):
  sa_type = JSONList


@model_field
class JSONDict(Field):
  sa_type = JSONDict


@model_field
class PhoneNumber(UnicodeText):
  pass


@model_field
class EmailAddress(UnicodeText):
  default_ff_type = 'EmailField'


@model_field
class URL(UnicodeText):
  default_ff_type = 'URLField'


@model_field
class Entity(Field):
  """
  Currently do nothing: must be implemented by subclassing generated model
  """
  def get_model_attributes(self, *args, **kwargs):
    return ()
