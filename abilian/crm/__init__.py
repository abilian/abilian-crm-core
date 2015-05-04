# coding=utf-8
"""
Abilian CRM package
"""
from __future__ import absolute_import

import jinja2

from . import jinja_filters

def register_plugin(app):
  app.extensions['babel'].add_translations('abilian.crm')
  jinja_filters.init_filters(app)
  app.register_jinja_loaders(jinja2.PackageLoader(__name__, 'templates'))
