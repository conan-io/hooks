import os
import shutil
import textwrap
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save, mkdir


class TestKBH016(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                        {placeholder}
                        from conan import ConanFile
                        class AConan(ConanFile):
                            pass                       
                        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH016, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_shebang(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder=""))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[META LINES (KB-H016)] OK" in output

    def test_with_shebang(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="#!/usr/bin/env python"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [META LINES (KB-H016)] Shebang (#!) detected in your recipe" in output

    def test_with_coding(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="# -*- coding: utf-8 -*-"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [META LINES (KB-H016)] PEP 263 (encoding) is not allowed in the conanfile" in output

    def test_with_vim_config(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [META LINES (KB-H016)] vim editor configuration detected in your recipe" in output

    def test_skip_pylint(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="# pylint:skip-file"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [META LINES (KB-H016)] Pylint can not be skipped" in output