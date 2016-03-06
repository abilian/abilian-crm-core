# coding=utf-8
"""
"""
from __future__ import absolute_import

from .registry import model_field, form_field, get_field, get_formfield

# register fields
from . import (simple, formfields, vocabulary, entity, yearly, postaladdress,
               phonenumber)

__all__ = ("model_field", "form_field", "get_field", "get_formfield", "simple",
           "formfields", "vocabulary", "entity", "yearly", "postaladdress",
           "phonenumber")
