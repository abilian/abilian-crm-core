# coding=utf-8
""""""
from __future__ import absolute_import, print_function, unicode_literals

import logging
from typing import Text

import phonenumbers

from abilian.app import Application
from abilian.i18n import default_country

logger = logging.getLogger(__name__)


def format_phonenumber(number, international=True):
    # type: (Text, bool) -> Text
    """Format phone number for display.

    No formatting is applied if the number is not a valid phonenumber.

    :param number: the phone number to format.
    :param international: always use international format, unless number is in
    national format OR country is the same as app's default country.
    """
    country = default_country() or "FR"
    try:
        pn = phonenumbers.parse(number, country)
    except phonenumbers.NumberParseException:
        return number
    except BaseException:
        logger.exception(
            'error while applying jinja filter "phonenumber" ' "- filter ignored"
        )
        return number

    if not (phonenumbers.is_possible_number(pn) and phonenumbers.is_valid_number(pn)):
        return number

    fmt = phonenumbers.PhoneNumberFormat.INTERNATIONAL
    number_country = phonenumbers.region_code_for_country_code(pn.country_code)
    if not international and number_country == country:
        fmt = phonenumbers.PhoneNumberFormat.NATIONAL

    return phonenumbers.format_number(pn, fmt)


def init_filters(app):
    # type: (Application) -> None
    app.jinja_env.filters["phonenumber"] = format_phonenumber
