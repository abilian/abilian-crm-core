# coding=utf-8
"""
"""
from __future__ import absolute_import

import wtforms.fields
import wtforms.widgets as wtf_widgets

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
        super(BooleanField, self).setup_widgets(extra_args)

        if 'widget' not in extra_args:
            kwargs = {}
            options = self.data.get('widget_args', {})
            kwargs['on_off_mode'] = bool(options)
            if not isinstance(options, dict):
                options = {}

            kwargs['on_off_options'] = options
            extra_args['widget'] = aw_widgets.BooleanWidget(**kwargs)


@form_field
class DateField(FormField):
    ff_type = awbff.DateField


@form_field
class DateTimeField(FormField):
    ff_type = awbff.DateTimeField


@form_field
class DecimalField(FormField):
    ff_type = wtforms.fields.DecimalField


@form_field
class IntegerField(FormField):
    ff_type = wtforms.fields.IntegerField

    def __init__(self, model, data, *args, **kwargs):
        super(IntegerField, self).__init__(model, data, *args, **kwargs)
        if 'widget' not in data:
            data['widget'] = wtf_widgets.html5.NumberInput()


@form_field
class EmailField(TextField):

    def __init__(self, model, data, *args, **kwargs):
        super(EmailField, self).__init__(model, data, *args, **kwargs)
        if 'widget' not in data:
            data['widget'] = aw_widgets.EmailWidget()
        if 'view_widget' not in data:
            widget = data['widget']
            data['view_widget'] = (widget
                                   if isinstance(widget, aw_widgets.EmailWidget)
                                   else aw_widgets.EmailWidget())


@form_field
class URLField(TextField):

    def __init__(self, model, data, *args, **kwargs):
        super(URLField, self).__init__(model, data, *args, **kwargs)
        if 'widget' not in data:
            data['widget'] = wtf_widgets.html5.URLInput()
        if 'view_widget' not in data:
            data['view_widget'] = aw_widgets.URLWidget()


@form_field
class FileField(FormField):
    ff_type = awbff.FileField


@form_field
class ImageField(FileField):

    def __init__(self, model, data, *args, **kwargs):
        if 'widget' not in data:
            data['widget'] = aw_widgets.ImageInput()
        super(ImageField, self).__init__(model, data, *args, **kwargs)
