import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestIncludePath(ConanClientTestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestIncludePath, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def _get_output_for(self, paths_created, paths_declared, component=""):
        conanfile = textwrap.dedent(f"""\
            from conans import ConanFile
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
        tools.save('conanfile.py', content=conanfile)
        return self.conan(['create', '.', 'name/version@user/test'])


    def test_usual_include_path(self):
        output = self._get_output_for(paths_created=["include"], paths_declared = ["include"])
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)
        
    def test_usual_include_path_component(self):
        output = self._get_output_for(paths_created=["include"], paths_declared = ["include"], component="componentname")
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)

    def test_no_include_path(self):
        output = self._get_output_for(paths_created=[], paths_declared = [])
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)

    def test_include_path_not_declared(self):
        output = self._get_output_for(paths_created=["include", "include/foo"], paths_declared = ["include"])
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)
        
    def test_include_path_not_declared_component(self):
        output = self._get_output_for(paths_created=["include", "include/foo"], paths_declared = ["include"], component="componentname")
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)

    def test_include_path_not_created(self):
        output = self._get_output_for(paths_created=["include"], paths_declared = ["include", "include/foo"])
        self.assertIn("ERROR: [INCLUDE PATH DOES NOT EXIST (KB-H071)] Component name::name include dir 'include/foo'", output)
        
    def test_include_path_not_created_component(self):
        output = self._get_output_for(paths_created=["include"], paths_declared = ["include", "include/foo"], component="componentname")
        self.assertIn("ERROR: [INCLUDE PATH DOES NOT EXIST (KB-H071)] Component name::componentname include dir 'include/foo'", output)
    
    def test_several_include_path(self):
        output = self._get_output_for(paths_created=["include", "include/bar"], paths_declared = ["include", "include/bar"])
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)
        
    def test_several_include_path_component(self):
        output = self._get_output_for(paths_created=["include", "include/bar"], paths_declared = ["include", "include/bar"], component="componentname")
        self.assertIn("[INCLUDE PATH DOES NOT EXIST (KB-H071)] OK", output)
