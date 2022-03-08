import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestRelocatableLibraries(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            exports_sources = "CMakeLists.txt"
            generatos = "cmake"
        """)
    cmakefile = textwrap.dedent("""\
        cmake_minimum_required(VERSION 3.1)
        project(cmake_wrapper)
        include(conanbuildinfo.cmake)
        conan_basic_setup(KEEP_RPATHS)
        add_subdirectory(source_subfolder)
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestRelocatableLibraries, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_with_keep_rpaths(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('CMakeLists.txt', content=self.cmakefile)
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[RELOCATABLE SHARED LIBS (KB-H071)] OK", output)
        self.assertNotIn("WARN: [RELOCATABLE SHARED LIBS (KB-H071)]", output)

    def test_without_keep_rpaths(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('CMakeLists.txt', content=self.cmakefile.replace("KEEP_RPATHS", ""))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[RELOCATABLE SHARED LIBS (KB-H071)] OK", output)
        self.assertIn("WARN: [RELOCATABLE SHARED LIBS (KB-H071)] Did not find "
                      "'conan_basic_setup(KEEP_RPATHS)' in CMakeLists.txt. "
                      "Update your CMakeLists.txt.", output)
