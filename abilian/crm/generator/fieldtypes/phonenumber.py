# coding=utf-8
"""
"""
from __future__ import absolute_import

import sqlalchemy as sa
from ...models import PhoneNumber
from ...forms import PhoneNumberField
from .registry import model_field, form_field
from .base import Field, FormField


@model_field
class _PhoneNumberField(Field):
  __fieldname__ = 'PhoneNumber'
  sa_type = sa.Integer
  default_ff_type = 'PhoneNumberFormField'
  allow_multiple = False

  def get_model_attributes(self, *args, **kwargs):
    # column declared_attr
    col_name = self.name + '_id'

    def gen_column(cls):
      fk_kw = dict(
        name=u'{}_{}_fkey'.format(cls.__name__.lower(), col_name),
        use_alter=True,
        ondelete = 'SET NULL',
      )
      target_col = str(PhoneNumber.id.parent.c.id)      
      fk = sa.ForeignKey(target_col, **fk_kw)
      return sa.Column(col_name, sa.types.Integer(), fk)

    gen_column.func_name = col_name
    yield col_name, sa.ext.declarative.declared_attr(gen_column)

    # relationship declared_attr
    def gen_relationship(cls):
      kw = dict(uselist=False)
      local = cls.__name__ + '.' + col_name
      remote = str(PhoneNumber.id)
      kw['primaryjoin'] = '{} == {}'.format(local, remote)
      return sa.orm.relationship(PhoneNumber, **kw)

    gen_relationship.func_name = self.name
    yield self.name, sa.ext.declarative.declared_attr(gen_relationship)
        

@form_field
class PhoneNumberFormField(FormField):
  ff_type = PhoneNumberField
  
