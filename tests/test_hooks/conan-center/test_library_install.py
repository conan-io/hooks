import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestInstalledLibraries(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        import os

        class AConan(ConanFile):
            settings = "os"

            def package(self):
                os.makedirs(os.path.join(self.package_folder, "lib"))
                open(os.path.join(self.package_folder, "lib", "libfoo.a"), "w")

            def package_info(self):
                self.cpp_info.libs = []
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestInstalledLibraries, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_library_doesnot_exist(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[LIBRARY DOES NOT EXIST (KB-H054)] OK", output)

    def test_empty_library_list(self):
        tools.save('conanfile.py', content=self.conanfile.replace("open", "# open"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[LIBRARY DOES NOT EXIST (KB-H054)] OK", output)

    def test_not_installed_global_library(self):
        tools.save('conanfile.py', content=self.conanfile.replace("[]", "['bar']"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [LIBRARY DOES NOT EXIST (KB-H054)] Component name::name library 'bar' is listed in the recipe, "
                      "but not found installed in cpp_info.libdirs.", output)

    def test_empty_component_libs(self):
        tools.save('conanfile.py', content=self.conanfile.replace("libs", "components['fake'].libs"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[LIBRARY DOES NOT EXIST (KB-H054)] OK", output)

    def test_empty_component_without_libs(self):
        tools.save('conanfile.py', content=self.conanfile.replace("libs", "components['fake'].libs")
                                                    .replace("open", "# open"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[LIBRARY DOES NOT EXIST (KB-H054)] OK", output)

    def test_not_install_component_libs(self):
        tools.save('conanfile.py', content=self.conanfile.replace("libs = []",
                                                             "components['fake'].libs = ['bar']"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [LIBRARY DOES NOT EXIST (KB-H054)] Component name::fake library 'bar' is listed in the recipe, "
                      "but not found installed in cpp_info.libdirs.", output)

    def test_header_only(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            no_copy_source = True
            def package_id(self):
                self.info.header_only()
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[LIBRARY DOES NOT EXIST (KB-H054)] OK", output)
