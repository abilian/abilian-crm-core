# coding=utf-8
"""
"""
from __future__ import absolute_import

from functools import partial


class Registrable(object):
    #: if not `None`, this is used as __fieldtype__()
    __fieldname__ = None

    @classmethod
    def __fieldtype__(cls):
        """
        :return: identifier name for this field type
        """
        return (cls.__fieldname__
                if cls.__fieldname__ is not None else cls.__name__)


_SA_FIELD_REGISTRY = dict()
_FF_FIELD_REGISTRY = dict()


def _register(registry, cls):
    """
    class decorator for `Registrable` subclasses
    """
    assert issubclass(cls, Registrable)
    reg_attr = '_{}_registered'.format(cls.__name__)
    if getattr(cls, reg_attr, False):
        return cls
    name = cls.__fieldtype__()

    assert name not in registry, (
        '{!r} cannot be registered as {!r}: already used by {!r}'
        ''.format(cls, name, registry[name]))
    registry[name] = cls
    setattr(cls, reg_attr, True)
    return cls


model_field = partial(_register, _SA_FIELD_REGISTRY)
form_field = partial(_register, _FF_FIELD_REGISTRY)

get_field = _SA_FIELD_REGISTRY.get
get_formfield = _FF_FIELD_REGISTRY.get
