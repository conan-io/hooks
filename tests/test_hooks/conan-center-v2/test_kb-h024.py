import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH024(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import save
            import os

            class AConan(ConanFile):
                settings = "os"

                def package(self):
                    save(self, os.path.join(self.package_folder, "lib", "libfoo.a"), "w")

                def package_info(self):
                    self.cpp_info.libs = []
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH024, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def setup_method(self, method):
        self.conan(['profile', 'detect', '--force'])

    def test_library_doesnot_exist(self):
        save(self, 'conanfile.py', content=self.conanfile)
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[LIBRARY DOES NOT EXIST (KB-H024)] OK" in output

    def test_empty_library_list(self):
        save(self, 'conanfile.py', content=self.conanfile.replace("open", "# open"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[LIBRARY DOES NOT EXIST (KB-H024)] OK" in output

    def test_not_installed_global_library(self):
        save(self, 'conanfile.py', content=self.conanfile.replace("[]", "['bar']"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [LIBRARY DOES NOT EXIST (KB-H024)] Component name::name library 'bar'" in output

    def test_empty_component_libs(self):
        save(self, 'conanfile.py', content=self.conanfile.replace("libs", "components['fake'].libs"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[LIBRARY DOES NOT EXIST (KB-H024)] OK" in output

    def test_empty_component_without_libs(self):
        save(self, 'conanfile.py', content=self.conanfile.replace("libs", "components['fake'].libs")
                   .replace("open", "# open"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[LIBRARY DOES NOT EXIST (KB-H024)] OK" in output

    def test_not_install_component_libs(self):
        save(self, 'conanfile.py', content=self.conanfile.replace("libs = []",
                                                                  "components['fake'].libs = ['bar']"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [LIBRARY DOES NOT EXIST (KB-H024)] Component name::name library 'bar' is listed in the recipe" in output

    def test_header_only(self):
        conanfile = textwrap.dedent("""\
        from conan import ConanFile
        class AConan(ConanFile):
            no_copy_source = True
            def package_id(self):
                self.info.clear()
        """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[LIBRARY DOES NOT EXIST (KB-H024)] OK" in output

    def test_full_library(self):
        save(self, 'conanfile.py', content=self.conanfile.replace("[]", "['libfoo.a']"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[LIBRARY DOES NOT EXIST (KB-H024)] OK" in output