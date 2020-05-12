""""""

import pytest

from .base import assert_valid_identifier


def test_assert_valid_identifier():
    avi = assert_valid_identifier
    avi("a")
    avi("ab_C42")
    avi("_a1")

    invalid = ("a test", "été", "a$" "@var", "newline\n")

    for ident in invalid:
        with pytest.raises(ValueError):
            print(ident)
            avi(ident)
