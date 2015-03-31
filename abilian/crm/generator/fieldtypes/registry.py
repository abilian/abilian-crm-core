# coding=utf-8
"""
"""
from __future__ import absolute_import

from .base import Field

_FIELD_REGISTRY = dict()

def register_field(cls):
  """
  class decorator for `.base.Field`
  """
  assert issubclass(cls, Field)
  reg_attr = '_{}_registered'.format(cls.__name__)
  if getattr(cls, reg_attr, False):
    return cls
  name = cls.__fieldtype__()
  assert name not in _FIELD_REGISTRY
  _FIELD_REGISTRY[name] = cls
  setattr(cls, reg_attr, True)
  return cls
  

get_field = _FIELD_REGISTRY.get
