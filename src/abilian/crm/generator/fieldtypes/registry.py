""""""

from functools import partial
from typing import Dict, Optional, Text


class Registrable:
    #: if not `None`, this is used as __fieldtype__()
    __fieldname__ = None  # type: Optional[Text]

    @classmethod
    def __fieldtype__(cls):
        """
        :return: identifier name for this field type
        """
        return cls.__fieldname__ if cls.__fieldname__ is not None else cls.__name__


_SA_FIELD_REGISTRY = dict()  # type: Dict[Text, Registrable]
_FF_FIELD_REGISTRY = dict()  # type: Dict[Text, Registrable]


def _register(registry, cls):
    """class decorator for `Registrable` subclasses."""
    assert issubclass(cls, Registrable)

    reg_attr = f"_{cls.__name__}_registered"
    if getattr(cls, reg_attr, False):
        return cls

    name = cls.__fieldtype__()
    assert (
        name not in registry
    ), f"{cls!r} cannot be registered as {name!r}: already used by {registry[name]!r}"

    registry[name] = cls
    setattr(cls, reg_attr, True)
    return cls


model_field = partial(_register, _SA_FIELD_REGISTRY)
form_field = partial(_register, _FF_FIELD_REGISTRY)

get_field = _SA_FIELD_REGISTRY.get
get_formfield = _FF_FIELD_REGISTRY.get
