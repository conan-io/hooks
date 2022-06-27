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

    conan_file_info = textwrap.dedent("""\
                import os
                from conans import ConanFile, tools

                class AConan(ConanFile):

                    def package(self):
                        tools.save(os.path.join(self.package_folder, {}), "foo")

                    def package_info(self):
                        self.cpp_info.builddirs = {}
                """)

    def _get_environ(self, **kwargs):
        kwargs = super(ConanCMakeBadFiles, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_find_and_config_files(self):

        tools.save('conanfile.py', content=self.conan_file.format("", "WhateverConfig.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [CMAKE-MODULES-CONFIG-FILES (KB-H016)] Found files: ./WhateverConfig.cmake",
                      output)

    def test_find_and_find_files(self):
        tools.save('conanfile.py', content=self.conan_file.format("", "FindXXX.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [CMAKE-MODULES-CONFIG-FILES (KB-H016)] Found files: ./FindXXX.cmake",
                      output)

    def test_find_and_find_files_and_config_files(self):
        conanfile = textwrap.dedent("""\
            import os
            from conans import ConanFile, tools

            class AConan(ConanFile):

                def package(self):
                    tools.save(os.path.join(self.package_folder, "FindXXX.cmake"), "foo")
                    tools.save(os.path.join(self.package_folder, "XXXConfig.cmake"), "foo")
            """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [CMAKE-MODULES-CONFIG-FILES (KB-H016)] Found files: ./FindXXX.cmake; ./XXXConfig.cmake",
                      output)

    def test_find_files_outside_dir(self):

        tools.save('conanfile.py', content=self.conan_file.format("folder", "file.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)] Found files: "
                      "./folder/file.cmake", output.replace("\\", "/"))

        tools.save('conanfile.py', content=self.conan_file.format("", "file.cmake"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)

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
        self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)

        tools.save('conanfile.py', content=conanfile2.format("some_build_dir/subdir"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)

    def test_good_files(self):
        tools.save('conanfile.py', content=self.conan_file_info.format('os.path.join("lib", "cmake", "script.cmake")', '["lib/cmake"]'))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)

        if tools.os_info.is_windows:
            tools.save('conanfile.py', content=self.conan_file_info.format('os.path.join("lib", "cmake", "script.cmake")', '["lib\\cmake"]'))
            output = self.conan(['create', '.', 'name/version@user/channel'])
            self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)

    def test_components(self):
        conanfile = textwrap.dedent("""\
                import os
                from conans import ConanFile, tools
                class AConan(ConanFile):
                    def package(self):
                        tools.save(os.path.join(self.package_folder, 'lib', 'cmake', 'FooBar.cmake'), "foo")

                    def package_info(self):
                        self.cpp_info.names["cmake_find_package"] = "foobar"
                        self.cpp_info.components["baz"].names["cmake_find_package"] = "baz"
                        self.cpp_info.components["baz"].names["cmake_find_package_multi"] = "baz"
                        self.cpp_info.components["baz"].builddirs = [os.path.join("lib", "cmake")]
                """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)

    def test_files_in_build_modules(self):
        conanfile = textwrap.dedent("""\
                import os
                from conans import ConanFile, tools

                class AConan(ConanFile):
                    @property
                    def _module_subfolder(self):
                        return os.path.join("lib", "cmake")

                    @property
                    def _module_file_rel_path(self):
                        return os.path.join(self._module_subfolder, f"conan-official-package-targets.cmake")

                    def package(self):
                        tools.save(os.path.join(self.package_folder, self._module_file_rel_path),
                                   "foo")

                    def package_info(self):
                        self.cpp_info.build_modules["cmake_find_package"] = [self._module_file_rel_path]
                        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
                """)

        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [CMAKE FILE NOT IN BUILD FOLDERS (KB-H019)]", output)
