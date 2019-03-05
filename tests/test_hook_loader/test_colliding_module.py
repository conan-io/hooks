# coding=utf-8

import os
import textwrap
import unittest

import six

from conans import tools
from tests.utils.environ_vars import context_env
from tests.utils.test_cases.conan_client import ConanClientTestCase


def _create_hook(tempfolder, hook_filename, value, add_init):
    func_file = textwrap.dedent("""
        def get_number():
            return {}
    """.format(value))

    hook_file = textwrap.dedent("""
        from utils.func import get_number

        def pre_export(output, conanfile, *args, **kwargs):
            output.info(">>>> {}")
            output.info(">>>> {{}}".format(get_number()))
    """.format(hook_filename))

    tools.save(os.path.join(tempfolder, hook_filename + '.py'), hook_file)
    tools.save(os.path.join(tempfolder, "utils", "func.py"), func_file)
    if add_init:
        tools.save(os.path.join(tempfolder, "utils", "__init__.py"), "")

    return os.path.join(tempfolder, hook_filename)


class CollidingModuleTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            pass
        """)

    @unittest.skipIf(six.PY2, "Python 2 requires __init__.py file in modules")
    def test_py3_colliding_module(self):
        hook1 = _create_hook(self._gimme_tmp(), "hook1", "42", add_init=False)
        hook2 = _create_hook(self._gimme_tmp(), "hook2", "23", add_init=False)

        with context_env(CONAN_HOOKS=','.join([hook1, hook2, ])):
            tools.save('conanfile.py', content=self.conanfile)
            output = self.conan(['export', '.', 'name/version@jgsogo/test'])

        self.assertIn(">>>> hook1", output)
        self.assertIn(">>>> 42", output)

        self.assertIn(">>>> hook2", output)
        self.assertIn(">>>> 23", output)

    def test_colliding_module(self):
        hook1 = _create_hook(self._gimme_tmp(), "hook1", "42", add_init=True)
        hook2 = _create_hook(self._gimme_tmp(), "hook2", "23", add_init=True)

        with context_env(CONAN_HOOKS=','.join([hook1, hook2, ])):
            tools.save('conanfile.py', content=self.conanfile)
            output = self.conan(['export', '.', 'name/version@jgsogo/test'])

        self.assertIn(">>>> hook1", output)
        self.assertIn(">>>> 42", output)

        self.assertIn(">>>> hook2", output)
        self.assertIn(">>>> 23", output)
