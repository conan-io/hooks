import os
import textwrap
import unittest

from conans import __version__ as conan_version
from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase


@unittest.skipUnless(conan_version >= "1.16.0", "Conan > 1.16.0 needed")
class ConanCMakeBadFiles(ConanClientTestCase):

    conan_file = textwrap.dedent("""\
                import os
                from conans import ConanFile, tools

                class AConan(ConanFile):

                    def package(self):
                        tools.save(os.path.join(self.package_folder, "{}", "{}"), "foo")
                """)

    def _get_environ(self, **kwargs):
        kwargs = super(ConanCMakeBadFiles, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_find_and_config_files(self):

        tools.save('conanfile.py', content=self.conan_file.format("", "WhateverConfig.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [CMAKE-MODULES-CONFIG-FILES] Found files:\n./WhateverConfig.cmake",
                      output)

    def test_find_and_find_files(self):

        tools.save('conanfile.py', content=self.conan_file.format("", "FindXXX.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [CMAKE-MODULES-CONFIG-FILES] Found files:\n./FindXXX.cmake",
                      output)

    def test_find_files_outside_dir(self):

        tools.save('conanfile.py', content=self.conan_file.format("folder", "file.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [CMAKE FILE NOT IN BUILD FOLDERS] Found files:\n"
                      "./folder/file.cmake\n", output)

        tools.save('conanfile.py', content=self.conan_file.format("", "file.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [CMAKE FILE NOT IN BUILD FOLDERS]", output)

        conanfile2 = textwrap.dedent("""\
                import os
                from conans import ConanFile, tools
    
                class AConan(ConanFile):
    
                    def package(self):
                        tools.save(os.path.join(self.package_folder, "{}", "file.cmake"), 
                                   "foo")
                    def package_info(self):
                        self.cpp_info.builddirs = ["some_build_dir"]
                """)

        tools.save('conanfile.py', content=conanfile2.format("some_build_dir"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [CMAKE FILE NOT IN BUILD FOLDERS]", output)

        tools.save('conanfile.py', content=conanfile2.format("some_build_dir/subdir"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [CMAKE FILE NOT IN BUILD FOLDERS]", output)
