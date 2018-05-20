# coding=utf-8
""""""
from __future__ import absolute_import, division, print_function

import imp
import logging
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Dict, Text

from .codegen import CodeGenerator

logger = logging.getLogger(__name__)


def generate_module(fullname, **kw):
    # type: (Text, Dict) -> ModuleType
    """
    :param fullname: dotted name of the module to generate.
    """
    module = imp.new_module(fullname)

    parent_module_name, name = fullname.rsplit(".", 1)
    parent_module = import_module(parent_module_name)
    directory = Path(parent_module.__file__).parent
    directory = directory / name

    assert directory.exists() and directory.is_dir()
    module.__path__ = [str(directory)]  # noqa

    for yml in directory.glob(u"*.yml"):
        logger.info("Loading: %s", yml)
        with yml.open("rt", encoding="utf-8") as f:
            gen = CodeGenerator(yaml_file=f, **kw)

        gen.init_vocabularies(module)
        gen.gen_model(module)
        gen.gen_form(module)

    return module


class GeneratedModelsFinder(object):
    """Module finder for generated models."""

    def __init__(self):
        self.managed_modules = {}
        sys.meta_path.append(self)

    def manage_module(self, package, name, **kw):
        """Install module loader for 'package.name'."""
        fullname = package + "." + name
        self.managed_modules[fullname] = kw

    def find_module(self, fullname, path=None):
        """PEP 302 finder."""
        if fullname in self.managed_modules:
            return self
        return None

    def load_module(self, fullname):
        """PEP 302 loader."""
        if fullname not in self.managed_modules:
            raise ImportError

        module = generate_module(fullname, **self.managed_modules[fullname])
        module.__loader__ = self
        sys.modules[fullname] = module
        return module


_finder = GeneratedModelsFinder()
install_loader = _finder.manage_module
