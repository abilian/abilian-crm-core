# coding=utf-8
"""
"""
from __future__ import absolute_import

from mock import patch

from abilian.crm import jinja_filters

def test_format_phonenumber():
  fmt = jinja_filters.format_phonenumber

  with patch('abilian.crm.jinja_filters.default_country') as default_country:
    default_country.return_value = u'US'
    assert fmt(u'2025550166') == u'+1 202-555-0166'
    assert default_country.called
    assert fmt(u'202-555-0166') == u'+1 202-555-0166'
    assert fmt(u'2025550166', international=False) == u'(202) 555-0166'
    assert fmt(u'+33102030405') == u'+33 1 02 03 04 05'
    assert fmt(u'+33102030405', international=False) == u'+33 1 02 03 04 05'

    default_country.reset_mock()
    default_country.return_value = u'FR'
    assert fmt(u'+12025550166') == u'+1 202-555-0166'
    assert fmt(u'(00)12025550166') == u'+1 202-555-0166'
    assert fmt(u'+33102030405') == u'+33 1 02 03 04 05'
    assert fmt(u'+33102030405', international=False) == u'01 02 03 04 05'
    assert fmt(u'0102030405', international=False) == u'01 02 03 04 05'
