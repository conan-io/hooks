# coding=utf-8

import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class SettingsCheckerTests(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            {placeholder}
        """)
    conanfile_basic = conanfile_base.format(
        placeholder='settings = "os", "arch"')
    conanfile_mixed = conanfile_base.format(
        placeholder='settings = "os", "os_build"')

    def _get_environ(self, **kwargs):
        kwargs = super(SettingsCheckerTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(
            __file__), '..', '..', 'hooks', 'settings_checker')})
        return kwargs

    def test_conanfile_basic(self):
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertNotIn(
            "pre_export(): WARN: This package defines both 'os' and 'os_build'", output)
        self.assertNotIn(
            "pre_export(): WARN: Please use 'os' for libraries and 'os_build'", output)
        self.assertNotIn(
            "pre_export(): WARN: only for build-requires used for cross-building", output)

    def test_conanfile_mixed(self):
        tools.save('conanfile.py', content=self.conanfile_mixed)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn(
            "pre_export(): WARN: This package defines both 'os' and 'os_build'", output)
        self.assertIn(
            "pre_export(): WARN: Please use 'os' for libraries and 'os_build'", output)
        self.assertIn(
            "pre_export(): WARN: only for build-requires used for cross-building", output)
