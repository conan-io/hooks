import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.compat import save


class TestGlobalFinalNewLine(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            pass
        """)

    cmakelists = textwrap.dedent("""\
        cmake_minimum_required(VERSION 3.0)
        project(someproject)
        
        include(conanbuildinfo.cmake)
        conan_basic_setup()
        
        add_subdirectory(source_subfolder)
        """)

    csource = textwrap.dedent("""\
        #include <stdio.h>
        int main() {
            printf("Hello world\\n");
            return 0;
        }
        """)

    conandata_yml = textwrap.dedent("""\
        sources:
          3.14:
            url: "http://example.com/download/release-3.14.tar.gz"
            sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        """)

    config_yml = textwrap.dedent("""\
        versions:
          3.14:
            folder:all
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestGlobalFinalNewLine, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_no_newline_pysoure(self):
        save('conanfile.py', content=self.conanfile.strip())
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
        self.assertIn("does not end with an endline", output)

    def test_no_newline_cmakelists(self):
        save('conanfile.py', content=self.conanfile)
        save(os.path.join('CMakeLists.txt'), content=self.cmakelists.strip())
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
        self.assertIn("does not end with an endline", output)

    def test_no_newline_csource(self):
        save('conanfile.py', content=self.conanfile)
        save(os.path.join('test_package', 'test_package.c'), content=self.csource.strip())
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
        self.assertIn("does not end with an endline", output)

    def test_no_newline_yml(self):
        save('conanfile.py', content=self.conanfile)
        save(os.path.join('conandata.yml'), content=self.conandata_yml.strip())
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
        self.assertIn("does not end with an endline", output)

    def test_no_newline_config_yml(self):
        save(os.path.join('all', 'conanfile.py'), content=self.conanfile)
        save(os.path.join('config.yml'), content=self.config_yml.strip())
        output = self.conan(['export', 'all', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
        self.assertIn("does not end with an endline", output)

    def test_no_newline_in_build_file(self):
        save('conanfile.py', content=self.conanfile)
        save(os.path.join('test_package', 'build', 'some_file.txt'), 'some data')
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
        self.assertNotIn("does not end with an endline", output)

    def test_ok_usage(self):
        save(os.path.join('config.yml'), content=self.config_yml)
        save(os.path.join('all', 'conanfile.py'), content=self.conanfile)
        save(os.path.join('all', 'CMakeLists.txt'), content=self.cmakelists)
        save(os.path.join('all', 'test_package', 'test_package.c'), content=self.csource)
        save(os.path.join('all', 'conandata.yml'), content=self.conandata_yml)
        output = self.conan(['export', 'all', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [NO FINAL ENDLINE (KB-H041)]", output)
