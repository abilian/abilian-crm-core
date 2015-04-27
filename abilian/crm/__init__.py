# coding=utf-8
"""
Abilian CRM package
"""
from __future__ import absolute_import

def register_plugin(app):
  app.extensions['babel'].add_translations('abilian.crm')
