# coding=utf-8
"""
Set up listener to automatically set 'name' from various attributes.
"""
from __future__ import absolute_import

import string
from operator import attrgetter

import sqlalchemy as sa


def setup(cls, spec):
    """
    :param cls: an Entity based class
    :param spec: a valid python format string
    """
    parser = string.Formatter()
    attributes = {
        field: attrgetter(field)
        for text, field, format_spec, conversion in parser.parse(spec) if field
    }

    # event handler
    def auto_name(obj, new_val, old_val, initiator):
        """ Auto set name. """
        if new_val != old_val:
            key = initiator.key
            vals = {key: new_val}
            for attr, getter in attributes.iteritems():
                if attr != key:
                    val = getter(obj)
                    if val is None:
                        val = u''
                    vals[attr] = val

            obj.name = spec.format(**vals).strip()

    # install listener on attributes
    for attr in attributes.iterkeys():
        attr_impl = getattr(cls, attr)
        sa.event.listen(
            attr_impl,
            "set",
            auto_name,
            propagate=True,  # set listener on subclasses
            active_history=True,
            retval=False)
