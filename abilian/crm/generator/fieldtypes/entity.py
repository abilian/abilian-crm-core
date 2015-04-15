# coding=utf-8
"""
"""
from __future__ import absolute_import

import sqlalchemy as sa

import abilian.web.forms.fields as awbff
import abilian.web.forms.widgets as aw_widgets
from abilian.web.action import Endpoint

from .registry import model_field, form_field
from .base import Field, FormField


@model_field
class EntityField(Field):
  __fieldname__ = 'Entity'
  default_ff_type = 'EntityFormField'

  def __init__(self, model, data, *args, **kwargs):
    super(EntityField, self).__init__(model, data, *args, **kwargs)
    self.target_cls = str(data.get('target', 'Entity').strip()) or 'Entity'

  def get_model_attributes(self, *args, **kwargs):
    target_col = self.target_cls.lower() + '.id' # use tablename + '.id'
    col_name = self.name + '_id'
    type_args = self.data.get('type_args', {})

    res_iter = (self._m2m_relationship(target_col, col_name, type_args)
                if self.multiple
                else self._single_relationship(target_col, col_name, type_args))

    for result in res_iter:
      yield result

  def _single_relationship(self, target_col, col_name, type_args):
    # column
    def get_column_attr(func_name, col_name, target_cls_name, target_col):
      def gen_column(cls):
        # always use ALTER: when 2 entities reference each other it raises
        # CircularDependencyError:
        fk_kw = dict(use_alter=True,
                     name='{}_{}_fkey'.format(cls.__name__.lower(), col_name),)

        fk_kw['ondelete'] = 'SET NULL'
        fk = sa.ForeignKey(target_col, **fk_kw)
        return sa.schema.Column(col_name, sa.types.Integer(), fk)

      gen_column.func_name = func_name
      return gen_column

    attr = get_column_attr(col_name, col_name, self.target_cls, target_col)
    yield col_name, sa.ext.declarative.declared_attr(attr)

    # relationship
    def get_rel_attr(func_name, target_cls, col_name):
      def gen_relationship(cls):
        kw = dict(uselist=False)
        local = cls.__name__ + '.' + col_name
        remote = target_cls + '.id'
        if cls.__name__ == target_cls:
          local = 'foreign({})'.format(local)
          remote = 'remote({})'.format(remote)
        kw['primaryjoin'] = '{} == {}'.format(local, remote)

        if 'backref' in type_args:
          backref_name = type_args['backref']
          backref_kw = {}
          if isinstance(backref_name, dict):
            backref_kw.update(backref_name)
            backref_name = backref_kw.pop('name')

          kw['backref'] = sa.orm.backref(backref_name, **backref_kw)

        return sa.orm.relationship(target_cls, **kw)

      gen_relationship.func_name = func_name
      return gen_relationship

    attr = get_rel_attr(self.name, self.target_cls, col_name)
    yield self.name, sa.ext.declarative.declared_attr(attr)

  def _m2m_relationship(self, target_col, col_name, type_args):
    def get_m2m_attr(func_name, target_cls, secondary_tbl_name=None):
      def gen_m2m_relationship(cls):
        src_name = cls.__tablename__
        target_name = target_cls.lower()
        tbl_name = secondary_tbl_name
        if tbl_name is None:
          tbl_name = (src_name + '_' + func_name)
        local_src_col = cls.__name__.lower() + '_id'
        local_target_col = target_name + '_id'
        secondary_table = sa.Table(
            tbl_name,
            cls.metadata,
            sa.Column(local_src_col,
                      sa.ForeignKey(src_name + '.id')),
            sa.Column(local_target_col,
                      sa.ForeignKey(target_col)),
            sa.schema.UniqueConstraint(local_src_col, local_target_col),
        )
        return sa.orm.relationship(target_cls, secondary=secondary_table)

      gen_m2m_relationship.func_name = func_name
      return gen_m2m_relationship

    attr = get_m2m_attr(self.name, self.target_cls)
    yield self.name, sa.ext.declarative.declared_attr(attr)


@form_field
class EntityFormField(FormField):
  ff_type = awbff.JsonSelect2Field

  def __init__(self, model, data, *args, **kwargs):
    super(EntityFormField, self).__init__(model, data, *args, **kwargs)
    self.module_endpoint = data.get('endpoint', self.name.lower())

  def get_type(self, *args, **kwargs):
    return (awbff.JsonSelect2MultipleField
            if self.multiple
            else awbff.JsonSelect2Field)

  def get_extra_args(self, *args, **kwargs):
    extra_args = super(EntityFormField, self).get_extra_args(*args, **kwargs)
    target = extra_args['model_class'] = self.data['target']
    extra_args['ajax_source'] = Endpoint(target.lower() + '.json_search')
    extra_args['multiple'] = self.multiple
    return extra_args

  def setup_widgets(self, extra_args):
    extra_args['view_widget'] = aw_widgets.EntityWidget()
    extra_args['widget'] = aw_widgets.Select2Ajax(multiple=self.multiple)
