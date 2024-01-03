import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH031(ConanClientV2TestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH031, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def _get_output_for(self, paths_created, paths_declared, component=""):
        conanfile = textwrap.dedent(f"""\
            from conan import ConanFile
            import os
            class AConan(ConanFile):
                settings = "os"

                def package(self):
                    for p in {paths_created}:
                        os.makedirs(os.path.join(self.package_folder, p))

                def package_info(self):
                    if {bool(component)}:
                        self.cpp_info.components["{component}"].includedirs = {paths_declared}
                    else:
                        self.cpp_info.includedirs = {paths_declared}
            """)
        save(self, 'conanfile.py', content=conanfile)
        return self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])

    def test_usual_include_path(self):
        output = self._get_output_for(paths_created=["include"], paths_declared=["include"])
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output

    def test_usual_include_path_component(self):
        output = self._get_output_for(paths_created=["include"], paths_declared=["include"], component="componentname")
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output

    def test_no_include_path(self):
        output = self._get_output_for(paths_created=[], paths_declared=[])
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output

    def test_include_path_not_declared(self):
        output = self._get_output_for(paths_created=["include", "include/foo"], paths_declared=["include"])
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output

    def test_include_path_not_declared_component(self):
        output = self._get_output_for(paths_created=["include", "include/foo"], paths_declared=["include"], component="componentname")
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output

    def test_include_path_not_created(self):
        output = self._get_output_for(paths_created=["include"], paths_declared=["include", "include/foo"])
        assert "ERROR: [INCLUDE PATH DOES NOT EXIST (KB-H031)] Component name::name" in output

    def test_include_path_not_created_component(self):
        output = self._get_output_for(paths_created=["include"], paths_declared=["include", "include/foo"], component="componentname")
        assert "ERROR: [INCLUDE PATH DOES NOT EXIST (KB-H031)] Component name::name include dir" in output

    def test_several_include_path(self):
        output = self._get_output_for(paths_created=["include", "include/bar"],
                                      paths_declared=["include", "include/bar"])
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output

    def test_several_include_path_component(self):
        output = self._get_output_for(paths_created=["include", "include/bar"],
                                      paths_declared=["include", "include/bar"], component="componentname")
        assert "[INCLUDE PATH DOES NOT EXIST (KB-H031)] OK" in output