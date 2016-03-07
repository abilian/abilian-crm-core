# coding=utf-8
"""
"""
from __future__ import absolute_import

from abilian.web.action import FAIcon
from abilian.web.forms.widgets import TextInput

from .jinja_filters import format_phonenumber


class PhoneNumberWidget(TextInput):
    pre_icon = FAIcon('phone')

    def render_view(self, field, **kwargs):
        data = field.data
        if not data:
            return u''

        return format_phonenumber(data, international=True)
