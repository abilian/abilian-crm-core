# coding=utf-8
"""Set up listener to automatically set 'name' from various attributes."""
from __future__ import absolute_import, print_function

import string
from operator import attrgetter
from typing import Text

import sqlalchemy as sa
import sqlalchemy.event

from abilian.core.entities import Entity


def setup(cls, spec):
    # type: (Entity, Text) -> None
    """
    :param cls: an Entity based class
    :param spec: a valid python format string
    """
    parser = string.Formatter()
    attributes = {
        field: attrgetter(field)
        for text, field, format_spec, conversion in parser.parse(spec)
        if field
    }

    # event handler
    def auto_name(obj, new_val, old_val, initiator):
        """Auto set name."""
        if new_val != old_val:
            key = initiator.key
            vals = {key: new_val}
            for attr, getter in attributes.items():
                if attr != key:
                    val = getter(obj)
                    if val is None:
                        val = u""
                    vals[attr] = val

            obj.name = spec.format(**vals).strip()

    # install listener on attributes
    for attr in attributes.keys():
        attr_impl = getattr(cls, attr)
        sa.event.listen(
            attr_impl,
            "set",
            auto_name,
            propagate=True,  # set listener on subclasses
            active_history=True,
            retval=False,
        )
