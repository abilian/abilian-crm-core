"""Abilian CRM package."""


def register_plugin(app):
    from .extension import crm

    crm.init_app(app)
