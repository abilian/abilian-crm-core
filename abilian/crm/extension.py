# coding=utf-8
"""
"""
from __future__ import absolute_import

import jinja2
import pkg_resources

from abilian.core.signals import register_js_api
from abilian.core.util import fqcn
from abilian.web import url_for

from . import jinja_filters
from .excel.views import bp as excel_bp

STATIC_DIR = pkg_resources.resource_filename(__name__, 'static')
JS = ('js/async_export.js',)


class AbilianCRM(object):
    """
    Base extension required by abilian.crm.apps
    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if FQCN in app.extensions:
            return

        app.extensions[FQCN] = self
        app.register_blueprint(excel_bp, url_prefix='/crm/excel')

        # register i18n
        app.extensions['babel'].add_translations('abilian.crm')

        jinja_filters.init_filters(app)
        app.register_jinja_loaders(jinja2.PackageLoader(__name__, 'templates'))

        # crm static assets
        app.add_static_url(
            'abilian/crm', STATIC_DIR, endpoint='abilian_crm_static')
        app.extensions['webassets'].append_path(
            STATIC_DIR, app.static_url_path + '/abilian/crm')

        app.register_asset('js', *JS)
        register_js_api.connect(self.register_js_api)

    def register_js_api(self, sender):
        app = sender
        js_api = app.js_api.setdefault('crm', {})
        js_api = js_api.setdefault('excel', {})
        js_api['taskStatusUrl'] = url_for('crm_excel.task_status')


FQCN = fqcn(AbilianCRM)
crm = AbilianCRM()
