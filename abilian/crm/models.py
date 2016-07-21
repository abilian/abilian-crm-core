# coding=utf-8
"""
"""
from __future__ import absolute_import

import sqlalchemy as sa

from abilian.core.models import IdMixin, Model

from .jinja_filters import format_phonenumber


class PostalAddress(IdMixin, Model):
    __tablename__ = 'crm_postal_address'

    #: Multi-lines field
    street_lines = sa.Column(sa.UnicodeText)
    #: State / Province / Region / Military PO /...
    administrative_area = sa.Column(sa.UnicodeText)
    #: County / District
    sub_administrative_area = sa.Column(sa.UnicodeText)
    #: City / Town
    locality = sa.Column(sa.UnicodeText)
    #: Postal code / ZIP code
    postal_code = sa.Column(sa.UnicodeText)
    #: Country ISO code
    country = sa.Column(sa.UnicodeText, nullable=False)

    __table_args__ = (
        # we DO require a country
        sa.schema.CheckConstraint(sa.sql.func.length(country) > 0),)


class PhoneNumber(IdMixin, Model):
    __tablename__ = 'crm_phonenumbers'

    #: number type: mobile, pro... left as free text
    type = sa.Column(
        sa.UnicodeText, default=u'', server_default=sa.sql.text(u"''"))
    #: phone number
    number = sa.Column(sa.UnicodeText, nullable=False)

    def __unicode__(self):
        if not self.number:
            self.number = u''
        if not self.type:
            self.type = u''
        return u'%s: %s' % (self.type, format_phonenumber(
            self.number, international=True))
