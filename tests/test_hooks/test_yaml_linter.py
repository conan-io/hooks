# coding=utf-8

import os
import textwrap
import unittest

from parameterized import parameterized

from conans import tools
from conans.client.command import ERROR_GENERAL, SUCCESS
from conans.tools import environment_append
from tests.utils.test_cases.conan_client import ConanClientTestCase


class YAMLLinterTests(ConanClientTestCase):
    conanfile = textwrap.dedent(r"""
        from conans import ConanFile, tools
        
        class TestConan(ConanFile):
            name = "name"
            version = "version"
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(YAMLLinterTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(
            __file__), '..', '..', 'hooks', 'yaml_linter')})
        return kwargs

    @parameterized.expand([(False, ), (True, )])
    def test_basic(self, yamllint_werr):
        conandatafile = textwrap.dedent(r"""
            sources:
            "version":
                url: "https://url.to/name/version.tar.xz"
                sha256: "3a530d1b243b5dec00bc54937455471aaa3e56849d2593edb8ded07228202240"
            patches:
            "version":
                - patch_file: "patches/abcdef.diff"
                  base_path: "source"
            patches:
            """)
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content=conandatafile)
        yamllint_werr_value = "1" if yamllint_werr else None
        with environment_append({"CONAN_YAMLLINT_WERR": yamllint_werr_value}):
            return_code = ERROR_GENERAL if yamllint_werr else SUCCESS
            output = self.conan(['export', '.', 'name/version@'], expected_return_code=return_code)

            if yamllint_werr:
                self.assertIn("pre_export(): Package recipe has YAML linter errors."
                              " Please fix them.", output)

            self.assertIn("conandata.yml:10:1:"
                          " [error] duplication of key \"patches\" in mapping (key-duplicates)",
                            output)

    def test_path_with_spaces(self):
        conandatafile = textwrap.dedent(r"""
            sources:
            "version":
                url: "https://url.to/name/version.tar.xz"
                sha256: "3a530d1b243b5dec00bc54937455471aaa3e56849d2593edb8ded07228202240"
            patches:
            "version":
                - patch_file: "patches/abcdef.diff"
                  base_path: "source"
            """)
        tools.save(os.path.join("path spaces", "conanfile.py"), content=self.conanfile)
        tools.save(os.path.join("path spaces", "conandata.py"), content=conandatafile)
        output = self.conan(['export', 'path spaces/conanfile.py', 'name/version@'])
        recipe_path = os.path.join(os.getcwd(), "path spaces", "conanfile.py")
        self.assertIn("pre_export(): Lint recipe '{}'".format(recipe_path), output)
        self.assertIn("pre_export(): Linter detected '0' errors", output)
