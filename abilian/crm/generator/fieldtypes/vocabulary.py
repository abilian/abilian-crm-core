# coding=utf-8
"""
"""
from __future__ import absolute_import

import sqlalchemy as sa

import abilian.web.forms.fields as awbff
import abilian.web.forms.widgets as aw_widgets

from .base import Field, FormField
from .registry import form_field, model_field


@model_field
class Vocabulary(Field):
    sa_type = sa.types.Integer
    default_ff_type = 'VocabularyFormField'

    def __init__(self, model, data, *args, **kwargs):
        super(Vocabulary, self).__init__(model, data, *args, **kwargs)
        self.voc_cls = data['vocabulary']['cls']

    def get_model_attributes(self, *args, **kwargs):
        relation_name = self.name
        attr_name = self.name + '_id'

        if not self.multiple:
            # column
            def get_column_attr(func_name, col_name, target_col):

                def gen_column(cls):
                    return sa.schema.Column(
                        col_name,
                        sa.ForeignKey(
                            target_col, ondelete='SET NULL'),)

                gen_column.func_name = func_name
                return gen_column

            attr = get_column_attr(attr_name, attr_name, self.voc_cls.id)
            yield attr_name, sa.ext.declarative.declared_attr(attr)

            # relationship
            def get_rel_attr(func_name, target_cls, attr_name):

                def gen_relationship(cls):
                    primary_join = '{} == {}'.format(
                        cls.__name__ + '.' + attr_name,
                        target_cls.__name__ + '.id')
                    return sa.orm.relationship(
                        target_cls, primaryjoin=primary_join)

                gen_relationship.func_name = func_name
                return gen_relationship

            attr = get_rel_attr(relation_name, self.voc_cls, attr_name)
            yield relation_name, sa.ext.declarative.declared_attr(attr)

        else:  # m2m

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
                        sa.Column(src_col, sa.ForeignKey(src_name + '.id')),
                        sa.Column('voc_id', sa.ForeignKey(target_name + '.id')),
                        sa.schema.UniqueConstraint(src_col, 'voc_id'),)
                    return sa.orm.relationship(
                        target_cls, secondary=secondary_table)

                gen_m2m_relationship.func_name = func_name
                return gen_m2m_relationship

            relation_secondary_tbl_name = \
                '{}_{}'.format(self.model.lower(), self.name.lower())

            rel_attr = get_m2m_attr(relation_name, self.voc_cls,
                                    relation_secondary_tbl_name)
            yield relation_name, sa.ext.declarative.declared_attr(rel_attr)


@form_field
class VocabularyFormField(FormField):
    ff_type = awbff.QuerySelect2Field

    def get_extra_args(self, *args, **kwargs):
        extra_args = super(VocabularyFormField, self) \
            .get_extra_args(*args, **kwargs)
        extra_args['multiple'] = self.multiple
        extra_args['get_label'] = 'label'

        def gen_voc_query(voc_cls):

            def query_voc():
                return voc_cls.query.active().all()

            query_voc.func_name = 'query_vocabulary_{}'.format(
                voc_cls.Meta.name)
            return query_voc

        voc_cls = self.data['vocabulary']['cls']
        extra_args['query_factory'] = gen_voc_query(voc_cls)
        return extra_args

    def setup_widgets(self, extra_args):
        extra_args['widget'] = aw_widgets.Select2(
            multiple=self.multiple, unescape_html=True)
        extra_args['view_widget'] = aw_widgets.ListWidget()
