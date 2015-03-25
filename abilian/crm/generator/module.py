# coding=utf-8
"""
"""
from __future__ import absolute_import

import sys
import imp
import logging
from importlib import import_module
from pathlib import Path

from .codegen import CodeGenerator

logger = logging.getLogger(__name__)


def generate_module(fullname):
  """
  :param module: existing module

  :param name: module name for generated classes

  :param directory: directory where resides *.yml files.
  By default, directory `name` in `module` directory.
  """
  module = imp.new_module(fullname)

  parent_module, name = fullname.rsplit('.', 1)
  parent_module = import_module(parent_module)
  directory = Path(parent_module.__file__).parent
  directory = directory / name

  assert directory.exists() and directory.is_dir()
  module.__path__ = [str(directory)]

  for yml in directory.glob(u'*.yml'):
    logger.info('Loading: %s', yml)
    with yml.open('r') as f:
      gen = CodeGenerator(yaml_file=f)

    gen.init_vocabularies(module)
    gen.gen_model(module)
    gen.gen_form(module)

  return module


class GeneratedModelsFinder(object):
  """
  Module finder for generated models
  """
  def __init__(self):
    self.managed_modules = set()
    sys.meta_path.append(self)

  def manage_module(self, package, name):
    """
    Install module loader for 'package.name'
    """
    fullname = package + '.' + name
    self.managed_modules.add(fullname)

  def find_module(self, fullname, path=None):
    """
    PEP 302 finder
    """
    if fullname in self.managed_modules:
      return self
    return None

  def load_module(self, fullname):
    """
    PEP 302 loader
    """
    if fullname not in self.managed_modules:
      raise ImportError

    module = generate_module(fullname)
    module.__loader__ = self
    sys.modules[fullname] = module
    return module


_finder = GeneratedModelsFinder()
install_loader = _finder.manage_module
