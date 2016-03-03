# coding=utf-8
"""
Abilian CRM package
"""
from __future__ import absolute_import


def register_plugin(app):
    from .extension import crm
    crm.init_app(app)
