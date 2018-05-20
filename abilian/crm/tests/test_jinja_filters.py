# coding=utf-8
""""""
from __future__ import absolute_import, print_function, unicode_literals

from mock import patch

from abilian.crm import jinja_filters


def test_format_phonenumber():
    fmt = jinja_filters.format_phonenumber

    with patch("abilian.crm.jinja_filters.default_country") as default_country:
        default_country.return_value = "US"
        assert fmt("2025550166") == "+1 202-555-0166"
        assert default_country.called
        assert fmt("202-555-0166") == "+1 202-555-0166"
        assert fmt("2025550166", international=False) == "(202) 555-0166"
        assert fmt("+33102030405") == "+33 1 02 03 04 05"
        assert fmt("+33102030405", international=False) == "+33 1 02 03 04 05"

        # "vanity" numbers:
        # phonenumbers lib can parse it as a valid number. Maybe we could
        # display both, one for keeping the "vanity" form, the other for
        # explicit numbers.
        assert fmt("(800) Flowers") == "+1 800-356-9377"
        assert fmt("1-800-Flowers", international=False) == "(800) 356-9377"

        default_country.reset_mock()
        default_country.return_value = "FR"
        assert fmt("+12025550166") == "+1 202-555-0166"
        assert fmt("(00)12025550166") == "+1 202-555-0166"
        assert fmt("+33102030405") == "+33 1 02 03 04 05"
        assert fmt("+33102030405", international=False) == "01 02 03 04 05"
        assert fmt("0102030405", international=False) == "01 02 03 04 05"

        # we want to avoid NumberParseException
        with patch("abilian.crm.jinja_filters.logger.exception") as logger:
            unparsable_text = 'garbage long unparsable text &"é(§è!çà)-)'
            assert fmt(unparsable_text) == unparsable_text
            assert not logger.called
