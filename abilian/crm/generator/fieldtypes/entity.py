# coding=utf-8
"""
"""
from __future__ import absolute_import

import sqlalchemy as sa
from abilian.core.entities import Entity as Entity

from .registry import model_field, form_field
from .base import Field, FormField


@model_field
class EntityField(Field):
  __fieldname__ = 'Entity'
  default_ff_type = 'EntityFormField'

  def __init__(self, data, *args, **kwargs):
    super(EntityField, self).__init__(data, *args, **kwargs)
    self.target_cls = str(data.get('target', 'Entity').strip()) or 'Entity'

    if self.multiple:
      raise ValueError(
        'field {}: multiples relations not supported for now'.format(
          repr(self.name))
      )
  
  def get_model_attributes(self, *args, **kwargs):
    target_col = self.target_cls.lower() + '.id' # use tablename + '.id'
    col_name = self.name + '_id'

    if not self.multiple:
      # column
      def get_column_attr(func_name, col_name, target_col):
        def gen_column(cls):
          return sa.schema.Column(col_name,
                                  sa.types.Integer(),
                                  sa.ForeignKey(target_col),
          )
        gen_column.func_name = func_name
        return gen_column

      attr = get_column_attr(col_name, col_name, target_col)
      yield col_name, sa.ext.declarative.declared_attr(attr)

      # relationship
      def get_rel_attr(func_name, target_cls, col_name):
        def gen_relationship(cls):
          primaryjoin = '{}.{} == {}.id'.format(cls.__name__, col_name,
                                                target_cls)         
          return sa.orm.relationship(
              target_cls,
              uselist=False,
              primaryjoin=primaryjoin,
          )

        gen_relationship.func_name = func_name
        return gen_relationship

      attr = get_rel_attr(self.name, self.target_cls, col_name)
      yield self.name, sa.ext.declarative.declared_attr(attr)
      
  def get_table_args(self, *args, **kwargs):
    if not self.multiple:
      local_col = self.name + '_id'
      target_col = self.target_cls.lower() + '.id' # use tablename + '.id'      
      fk = sa.schema.ForeignKeyConstraint(
        [local_col], [target_col],
        'fk_{}_{}'.format(self.name, self.target_cls.lower()),
        ondelete='SET NULL',
        use_alter=True,
      )
      yield fk

      
@form_field
class EntityFormField(FormField):
  pass
