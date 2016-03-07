# coding=utf-8
"""
"""
from __future__ import absolute_import

import logging

import phonenumbers

from abilian.i18n import default_country

logger = logging.getLogger(__name__)


def format_phonenumber(n, international=True):
    """Format phone number for display.

    No formatting is applied if the number is not a valid phonenumber.

    :param international: always use international format, unless number is in
    national format OR country is the same as app's default country.
    """
    country = default_country() or u'FR'
    try:
        pn = phonenumbers.parse(n, country)
    except phonenumbers.NumberParseException:
        return n
    except:
        logger.exception('error while applying jinja filter "phonenumber" '
                         '- filter ignored')
        return n

    if not (phonenumbers.is_possible_number(pn) and
            phonenumbers.is_valid_number(pn)):
        return n

    fmt = phonenumbers.PhoneNumberFormat.INTERNATIONAL
    number_country = phonenumbers.region_code_for_country_code(pn.country_code)
    if not international and number_country == country:
        fmt = phonenumbers.PhoneNumberFormat.NATIONAL

    return phonenumbers.format_number(pn, fmt)


def init_filters(app):
    app.jinja_env.filters['phonenumber'] = format_phonenumber
