""""""

from wtforms.fields import IntegerField, StringField, TextAreaField
from wtforms.widgets import HiddenInput

from abilian.i18n import _l, country_choices
from abilian.web.forms import ModelForm
from abilian.web.forms.fields import ModelFormField, Select2Field
from abilian.web.forms.filters import strip
from abilian.web.forms.validators import flaghidden, optional, required
from abilian.web.forms.widgets import ModelWidget, TextArea

from .models import PhoneNumber, PostalAddress
from .widgets import PhoneNumberWidget


class RequireableFormField:
    """Mixin for Formfield based class, to allow toggle required / optional.

    Basic FormField doesn't allow any validators, making harder to
    include an optional formfield with required fields.
    """

    def __init__(self, *args, **kwargs):
        self.__validators = tuple(kwargs.pop("validators", ()))
        super().__init__(*args, **kwargs)

        for v in self.__validators:
            for flag in getattr(v, "field_flags", ()):
                if flag == "required":
                    self.flags.required = True
                elif flag != "optional":
                    raise TypeError(
                        f'{self.__class__.__name__} accept only "required" validator'
                    )

    def process(self, *args, **kwargs):
        super().process(*args, **kwargs)

        for f in self.form:
            if f.flags.required:
                f.validators = self.__filter_validators(f)
                f.flags.required = self.flags.required
                f.flags.optional = not self.flags.required

    def __filter_validators(self, field):
        required = self.flags.required
        if required == field.flags.required:
            return field.validators

        validators = []
        remove = "optional" if required else "required"
        has_required = False

        for v in field.validators:
            if required and any(f == "required" for f in v.field_flags):
                has_required = True
            if any(f == remove for f in v.field_flags):
                continue
            validators.append(v)

        if required and not has_required:
            validators.append(required())

        return validators


class PhoneNumberField(StringField):
    widget = PhoneNumberWidget()


class PostalAddressForm(ModelForm):

    id = IntegerField(widget=HiddenInput(), validators=[optional(), flaghidden()])
    street_lines = TextAreaField(
        _l("postal_address_street_lines"),
        description=_l("postal_address_street_lines_help"),
        validators=[required()],
        filters=(strip,),
        widget=TextArea(rows=4),
    )

    administrative_area = StringField(
        _l("postal_address_administrative_area"),
        description=_l("postal_address_administrative_area_help"),
    )

    sub_administrative_area = StringField(
        _l("postal_address_sub_administrative_area"),
        description=_l("postal_address_sub_administrative_area_help"),
    )

    postal_code = StringField(
        _l("postal_address_postal_code"),
        description=_l("postal_address_postal_code_help"),
        validators=[required()],
        filters=(strip,),
    )

    locality = StringField(
        _l("postal_address_locality"),
        # description=_l(u'postal_address_locality_help'),
        validators=[required()],
        filters=(strip,),
    )

    country = Select2Field(
        _l("postal_address_country"),
        validators=[required()],
        filters=(strip,),
        choices=country_choices,
    )

    class Meta:
        model = PostalAddress
        include_primary_keys = True
        assign_required = False


class PostalAddressField(RequireableFormField, ModelFormField):
    widget = ModelWidget()

    def __init__(self, *args, **kwargs):
        super().__init__(PostalAddressForm, *args, **kwargs)


class PhoneNumberForm(ModelForm):
    id = IntegerField(widget=HiddenInput(), validators=[optional(), flaghidden()])
    type = StringField(_l("phonenumber_type"), description=_l("phonenumber_type_help"))
    number = PhoneNumberField(
        _l("phonenumber_number"),
        description=_l('for an extension number add "#1234"'),
        validators=[required()],
    )

    class Meta:
        model = PhoneNumber
        include_primary_keys = True
        assign_required = False


class PhoneNumberFormField(RequireableFormField, ModelFormField):
    widget = ModelWidget(view_template="crm/widgets/phonenumber_model_view.html")

    def __init__(self, *args, **kwargs):
        super().__init__(PhoneNumberForm, *args, **kwargs)
