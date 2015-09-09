# coding=utf-8
"""
Celery task for async export
"""
from __future__ import absolute_import

from itertools import ifilter
from urlparse import urlparse
from cStringIO import StringIO
from time import strftime, gmtime

from flask import current_app, request
from celery import shared_task
from flask_login import login_user

from abilian.core.models.subjects import User

from .util import XLSX_MIME

@shared_task(bind=True, track_started=True, ignore_result=False)
def export(self, app, module, from_url, user_id, component='excel'):
  """
  Async export xls task.

  :param app: `CRUDApp` name

  :param module: module id

  :param from_url: full url that started this task

  :param user_id: user's id for who this task is run
  """
  user = User.query.get(user_id)
  crud_app  = current_app.extensions[app]
  module = crud_app.get_module(module)
  component = module.get_component(component)
  url = urlparse(from_url)
  rq_ctx = current_app.test_request_context(
    base_url=u'{url.scheme}://{url.netloc}/{url.path}'.format(url=url),
    path=url.path,
    query_string=url.query,
  )

  def progress_callback(exported=0, total=0, **kw):
    self.update_state(state='PROGRESS',
                      meta={'exported': exported, 'total': total})

  uploads = current_app.extensions['uploads']

  with rq_ctx:
    login_user(user, remember=False, force=False)
    objects = module.ordered_query(request)
    related_cs = None
    manager = component.excel_manager(module.managed_class,
                                      component.export_form,
                                      component.EXCEL_EXPORT_RELATED)

    if 'related' in request.args:
      related = request.args['related']
      related_cs = ifilter(lambda cs: cs.related_attr == related,
                           component.EXCEL_EXPORT_RELATED)
      try:
        related_cs = next(related_cs)
      except StopIteration:
        related_cs = None

    workbook = manager.export(objects,
                              related_cs,
                              progress_callback=progress_callback)
    fd = StringIO()
    workbook.save(fd)
    fd.seek(0)
    # save in uploads dir, return handle needed for download
    filename = u"{}-{}.xlsx".format(module.managed_class.__name__,
                                    strftime("%d:%m:%Y-%H:%M:%S", gmtime()))
    handle = uploads.add_file(user, fd,
                              filename=filename,
                              mimetype=XLSX_MIME)
    return dict(handle=handle)
