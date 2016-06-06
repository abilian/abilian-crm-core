# coding=utf-8
"""
"""
from __future__ import absolute_import, print_function

import pytest

from .base import assert_valid_identifier


def test_assert_valid_identifier():
    avi = assert_valid_identifier
    avi(u'a')
    avi(u'ab_C42')
    avi(u'_a1')

    invalid = (u'a test', u'été', u'a$' u'@var', u'newline\n')

    for ident in invalid:
        with pytest.raises(ValueError):
            print(ident)
            avi(ident)
