# coding=utf-8
"""
"""
from __future__ import absolute_import

import wtforms.fields

import abilian.web.forms.fields as awbff
import abilian.web.forms.widgets as aw_widgets
from abilian.web.forms.filters import strip

from .base import FormField
from .registry import form_field

@form_field
class TextField(FormField):
  def get_filters(self, *args, **kwargs):
    return (strip,)


@form_field
class BooleanField(FormField):
  ff_type = wtforms.fields.BooleanField

  def get_validators(self, *args, **kwargs):
    # default implementation may add 'required'
    return ()
  
  def setup_widgets(self, extra_args):
    if 'widget' not in extra_args:
      extra_args['widget'] = aw_widgets.BooleanWidget()


@form_field
class DateField(FormField):
  ff_type = awbff.DateField


@form_field
class DecimalField(FormField):
  ff_type = wtforms.fields.DecimalField


@form_field
class IntegerField(FormField):
  ff_type = wtforms.fields.IntegerField


@form_field
class EmailField(TextField):

  def __init__(self, model, data, *args, **kwargs):
    super(EmailField, self).__init__(model, data)
    if 'view_widget' not in data:
      data['view_widget'] = aw_widgets.EmailWidget()


@form_field
class URLField(TextField):

  def __init__(self, model, data, *args, **kwargs):
    super(URLField, self).__init__(model, data)
    if 'view_widget' not in data:
      data['view_widget'] = aw_widgets.URLWidget()


