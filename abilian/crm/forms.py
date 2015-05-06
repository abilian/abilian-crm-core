# coding=utf-8
"""
"""
from __future__ import absolute_import

from wtforms.fields import StringField, TextAreaField, IntegerField
from wtforms.widgets import HiddenInput

from abilian.i18n import _l, country_choices
from abilian.web.forms import ModelForm
from abilian.web.forms.fields import Select2Field, ModelFormField
from abilian.web.forms.widgets import TextArea, ModelWidget
from abilian.web.forms.validators import required, flaghidden, optional
from abilian.web.forms.filters import strip

from .models import PostalAddress, PhoneNumber
from .widgets import PhoneNumberWidget


class PhoneNumberField(StringField):
  widget = PhoneNumberWidget()
  

class PostalAddressForm(ModelForm):

  id = IntegerField(widget=HiddenInput(), validators=[optional(), flaghidden()])  
  street_lines = TextAreaField(
    _l(u'postal_address_street_lines'),
    description=_l(u'postal_address_street_lines_help'),
    filters=(strip,),    
    widget=TextArea(rows=4, resizeable=None),
  )
  administrative_area = StringField(
    _l(u'postal_address_administrative_area'),
    description=_l(u'postal_address_administrative_area_help'),
  )
  sub_administrative_area = StringField(
    _l(u'postal_address_sub_administrative_area'),
    description=_l(u'postal_address_sub_administrative_area_help'),
  )
  locality = StringField(
    _l(u'postal_address_locality'),
    description=_l(u'postal_address_locality_help'),
  )
  postal_code = StringField(
    _l(u'postal_address_postal_code'),
    description=_l(u'postal_address_postal_code_help'),
  )
  
  country = Select2Field(
    _l(u'postal_address_country'),
    validators=[required()],
    filters=(strip,),
    choices=country_choices,
  )

  class Meta:
    model = PostalAddress
    include_primary_keys = True
    assign_required = False


class PostalAddressField(ModelFormField):
  widget = ModelWidget()
  
  def __init__(self, *args, **kwargs):
    if 'validators' in kwargs:
      del kwargs['validators']
    super(PostalAddressField, self).__init__(PostalAddressForm, *args, **kwargs)



class PhoneNumberForm(ModelForm):
  id = IntegerField(widget=HiddenInput(), validators=[optional(), flaghidden()])  
  type = StringField(
    _l(u'phonenumber_type'),
    description=_l(u'phonenumber_type_help'),
  )
  number = PhoneNumberField(
    _l(u'phonenumber_number'),
    validators=[required()],
  )
  
  class Meta:
    model = PhoneNumber
    include_primary_keys = True
    assign_required = False

    
class PhoneNumberField(ModelFormField):
  widget = ModelWidget(view_template='crm/widgets/phonenumber_model_view.html')

  def __init__(self, *args, **kwargs):
    if 'validators' in kwargs:
      del kwargs['validators']
    super(PhoneNumberField, self).__init__(PhoneNumberForm, *args, **kwargs)
  
