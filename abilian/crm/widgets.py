# coding=utf-8
"""
"""
from __future__ import absolute_import

from wtforms.widgets.core import TextInput

from .jinja_filters import format_phonenumber


class PhoneNumberWidget(TextInput):

  def render_view(self, field, **kwargs):
    data = field.data
    if not data:
      return u''
    
    return format_phonenumber(data, international=True)
