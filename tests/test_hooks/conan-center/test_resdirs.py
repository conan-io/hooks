# coding=utf-8

import os
import textwrap
import unittest

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase

here = os.path.dirname(__file__)


class VersionRanges(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile, tools
        import os

        class AConan(ConanFile):
            def package(self):
                for folder in {root_subfolders}:
                    tools.save(os.path.join(self.package_folder, folder, "some_text.txt"), "hello world\\n")
            def package_info(self):
                self.cpp_info.resdirs = {resdirs}                
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(VersionRanges, self)._get_environ(**kwargs)
        kwargs.update({"CONAN_HOOKS": os.path.join(here, "..", "..", "..", "hooks", "conan-center")})
        return kwargs

    def _create_package(self, root_subfolders, resdirs):
        tools.save("conanfile.py", content=self.conanfile.format(root_subfolders=root_subfolders, resdirs=resdirs))
        output = self.conan(["create", ".", "name/version@user/channel", "-tf", "None"])
        return output

    def test_root_include_resdirs_empty(self):
        output = self._create_package(root_subfolders=["include"], resdirs=[])
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)

    def test_root_share_resdirs_empty(self):
        output = self._create_package(root_subfolders=["share"], resdirs=[])
        self.assertNotIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
        self.assertIn("ERROR: [DEFAULT PACKAGE LAYOUT (KB-H013)] Unknown folder 'share' in the package", output)

    def test_root_share_resdirs_share(self):
        output = self._create_package(root_subfolders=["share"], resdirs=["share"])
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
