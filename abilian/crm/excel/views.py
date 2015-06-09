# coding=utf-8
"""
"""
from __future__ import absolute_import

import logging
import cStringIO as StringIO
from time import strftime, gmtime
from itertools import ifilter

from flask import request, current_app, flash, render_template, redirect

from abilian.i18n import _, _l
from abilian.web import views, csrf, url_for
from abilian.web.util import capture_stream_errors
from abilian.web.action import actions, Endpoint, FAIcon
from abilian.web.frontend import (
  ModuleView, ModuleAction, ModuleActionDropDown, ModuleActionGroupItem,
)

from .manager import ExcelManager

logger = logging.getLogger(__name__)

XLSX_MIME = u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class _ItemUpdate(object):
  """
  Holds item update data.
  
  Used in import views.

  :param item_id: primary key
  :param attrs: list of attributes, in received order
  :param signature: verify @attrs authenticity
  :param data: dict attr => new value. Keys must be in attrs
  """
  def __init__(self, item_id, attrs, signature, data):
    self.id = item_id
    self.attrs = sorted(attrs)
    self.sig = signature
    self.data = data


class BaseExcelView(ModuleView, views.View):
  """
  """
  excel_manager = ExcelManager

  def __init__(self, view_endpoint, *args, **kwargs):
    super(BaseExcelView, self).__init__(*args, **kwargs)
    self.view_endpoint = view_endpoint
    self.__manager = None
  
  def redirect_to_index(self):
    return redirect(self.view_endpoint)
  
  @property
  def excel_export_actions(self):
    actions = []
    for column_set in self.module.EXCEL_EXPORT_RELATED:
      actions.append(
        (url_for('.export_to_xls', related=column_set.related_attr),
         column_set.export_label)
      )

    return actions

  @property
  def manager(self):
    if self.__manager is None:
      self.__manager = self.excel_manager(self.module.managed_class,
                                          self.module.edit_form_class,
                                          self.module.EXCEL_EXPORT_RELATED)
    return self.__manager

  
class ExcelExport(BaseExcelView):
  """
  """
  def get(self):
    objects = []
    related_cs = None

    if 'import_template' not in request.args:
      objects = self.module.ordered_query(request)

    if 'related' in request.args:
      related = request.args['related']
      related_cs = ifilter(lambda cs: cs.related_attr == related,
                           self.module.EXCEL_EXPORT_RELATED)
      try:
        related_cs = next(related_cs)
      except StopIteration:
        related_cs = None

    # create manager now: inside 'response_generator' we cannot instantiate the
    # manager: flask raises "RuntimeError('working outside of application
    # context')"
    manager = self.manager

    @capture_stream_errors(logger, 'Error during XLS export')
    def response_generator():
      yield '' # start response stream before XLS build has started. For long
               # files this avoids having downstream http server returning proxy
               # error to client. Unfortunatly xlwt doesn't allow writing by
               # chunks
      workbook = manager.export(objects, related_cs)
      fd = StringIO.StringIO()
      workbook.save(fd)
      yield fd.getvalue()

    debug = request.args.get('debug_sql')
    if debug:
      # useful only in DEBUG mode, to get the debug toolbar in browser
      return '<html><body>Exported</body></html>'

    response = current_app.response_class(
        response_generator(),
        mimetype=XLSX_MIME,
    )
    filename = u"{}-{}.xlsx".format(self.module.managed_class.__name__,
                                    strftime("%d:%m:%Y-%H:%M:%S", gmtime()))
    response.headers['content-disposition'] = \
        'attachment;filename="{}"'.format(filename)

    return response

  
class ExcelImport(BaseExcelView):
  """
  """
  methods = ['POST']
  
  @csrf.protect
  def post(self):
    xls = request.files['file']
    try:
      xls.stream.seek(0, 2)
      size = xls.stream.tell()
      xls.stream.seek(0)
    except:
      size = 0

    if size == 0:
      flash('Import Excel: aucun fichier fourni', 'error')
      return self.redirect_to_index()

    @capture_stream_errors(logger, 'Error during XLS import')
    def generate():
      manager = self.manager
      filename = xls.filename
      modified_items = None
      error = False
      redirect_to = url_for('.list_view')

      try:
        modified_items = manager.import_data(xls,
                                             self.module.EXCEL_EXPORT_RELATED)
      except xlrd.XLRDError as e:
        error = True
        flash(_(u'Cannot read file {filename} as Excel file').format(
                filename=filename),
              'error')
        logger.error(e, exc_info=True)
      except ExcelError, e:
        error = True
        flash(e.message, 'error')

      if modified_items is not None and len(modified_items) == 0:
        flash(_(u'No change detected in file {filename}'.format(
          filename=filename)),
          u'info')

      yield render_template('crm/import_xls.html',
                            is_error=error,
                            redirect_to=redirect_to,
                            modified_items=modified_items,
                            excel=manager,
                            filename=filename)

    response = current_app.response_class(generate())
    return response


class ExcelImportValidate(BaseExcelView):
  """
  """
  methods=['POST']
  
  @csrf.protect
  def post(self):
    action = request.form.get('_action')

    if action != u'validate':
      flash(u'Annulé', 'info')
      return self.redirect_to_index()

    filename = request.form.get('filename')
    redirect_to = url_for('.list_view')

    @capture_stream_errors(logger, 'Error during XLS import validation')
    def generate():
      # build data from form values
      f = request.form
      data = []
      item_count = int(f.get('item_count'))

      for idx in range(1, item_count+1):
        key = 'item_{:d}_{{}}'.format(idx)
        item_id = f.get(key.format('id'))
        if item_id is not None:
          item_id = int(item_id)
        attrs = f.getlist(key.format('attrs'))
        sig = f.get(key.format('attrs_sig'))
        to_import = frozenset(f.getlist(key.format('import')))

        # fetch object attrs
        attrkey = key.format('attr') + '_{}'
        item_modified = {}
        for attr in attrs:
          if attr not in to_import:
            logger.debug('item %d: skip %s', idx, attr)
            continue
          value = f.get(attrkey.format(attr))
          item_modified[attr] = value

        # fetch 'many relateds' values'
        many_relateds_attrs = f.getlist(key.format('many_relateds_attrs'))
        many_relateds = {}

        for rel_attr in many_relateds_attrs:
          rkey = key.format(rel_attr) + '_{}'
          objs = []
          for ridx in range(1, int(f.get(rkey.format('count'), 0)) + 1):
            modified = {}
            robjkey = rkey.format(ridx) + '_{}'
            r_attrs = f.getlist(robjkey.format('attrs'))

            rattrkey = robjkey.format('attr_{}')
            for attr in r_attrs:
              modified[attr] = f.get(rattrkey.format(attr))

            objs.append(_ItemUpdate(None, r_attrs, '', modified))
          if objs:
            many_relateds[rel_attr] = objs

        if many_relateds:
          item_modified['__many_related__'] = many_relateds

        data.append(_ItemUpdate(item_id, attrs, sig, item_modified))

      result = self.manager.save_data(data)
      flash(_(u'Import from {filename}: {changed} items changed, '
              '{created} items created, '
              '{skipped} ignored due to errors').format(
                filename=filename,
                changed=result['changed_items'],
                created=result['created_items'],
                skipped=result['skipped_items']),
            'error' if result['error_happened'] else 'info'
        )

      yield render_template('crm/xls_data_saved.html',
                            redirect_to=redirect_to)

    response = current_app.response_class(generate())
    return response


class ExcelModuleMixin(object):
  """
  Mixin for :class:`abilian.web.frontend.Module` objects
  """
  EXCEL_SUPPORT_IMPORT = False

  #: tuple of ManyRelatedColumnSet()
  EXCEL_EXPORT_RELATED = ()
  
  def init_related_views(self):
    super(ExcelModuleMixin, self).init_related_views()
    self._setup_view('/export_xls', 'export_xls', ExcelExport,
                     module=self,
                     view_endpoint=self.endpoint + '.list_view',)

    if not self.EXCEL_SUPPORT_IMPORT:
      return
    
    self._setup_view('/validate_imported_data', 'validate_imported_xls',
                     ExcelImportValidate,
                     methods=['POST'],
                     module=self,
                     view_endpoint=self.endpoint + '.list_view',)
    
    self._setup_view('/import_xls', 'import_xls', ExcelImport,
                     methods=['POST'],
                     module=self,
                     view_endpoint=self.endpoint + '.list_view')

    
  def register_actions(self):
    super(ExcelModuleMixin, self).register_actions()

    excel_actions = []
    button = 'default' if not self.EXCEL_EXPORT_RELATED else None
    excel_actions.append(
      ModuleAction(self, 'excel', 'export_xls',
                   title=_(u'Export to Excel'), icon=FAIcon('align-justify'),
                   endpoint=Endpoint(self.endpoint + '.export_xls'),
                   button=button, css='datatable-export',))
    
    for column_set in self.EXCEL_EXPORT_RELATED:
      excel_actions.append(
        ModuleActionGroupItem(
          self, 'excel', 'export_related_' + column_set.related_attr,
          title=column_set.export_label, icon=FAIcon('align-justify'),
          css='datatable-export',
          endpoint=Endpoint(self.endpoint + '.export_xls',
                            related=column_set.related_attr),
          )
      )

    if self.EXCEL_SUPPORT_IMPORT:
      pass

    if len(excel_actions) > 1:
      excel_actions = [ModuleActionDropDown(
        self, 'excel', 'actions',
        title=_l(u'Excel'), button='default',
        items=excel_actions,
      )]
    
    actions.register(*excel_actions)
  
