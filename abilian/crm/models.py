# coding=utf-8
"""
"""
from __future__ import absolute_import

import sqlalchemy as sa
from abilian.core.models import Model, IdMixin


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
    sa.schema.CheckConstraint(sa.sql.func.length(country) > 0),
  )
  
