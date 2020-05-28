# coding=utf-8

import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class MembersTypoCheckerTests(ConanClientTestCase):
    conanfile_basic = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            name = "name"
            version = "version"
            def package_info(self):
                self.cpp_info.defines = ["ACONAN"]
        """)
    conanfile_with_typos = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            name = "name"
            version = "version"

            exports_sourcess = "OH_NO"

            require = "Hello/0.1@oh_no/stable"

            def requirement(self):
                self.requires("Hello/0.1@oh_no/stable")

            def package_info(self):
                self.cpp_info.defines = ["ACONAN"]
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(MembersTypoCheckerTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(
            __file__), '..', '..', 'hooks', 'members_typo_checker')})
        return kwargs

    def test_conanfile_basic(self):
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertNotIn("member looks like a typo", output)

    def test_conanfile_with_typos(self):
        tools.save('conanfile.py', content=self.conanfile_with_typos)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn(
            "pre_export(): WARN: The 'exports_sourcess' member looks like a typo. Similar to:", output)
        self.assertIn(
            "pre_export(): WARN:     exports_sources", output)
        self.assertIn(
            "pre_export(): WARN: The 'require' member looks like a typo. Similar to:", output)
        self.assertIn(
            "pre_export(): WARN:     requires", output)
        self.assertIn(
            "pre_export(): WARN: The 'requirement' member looks like a typo. Similar to:", output)
        self.assertIn(
            "pre_export(): WARN:     requirements", output)
