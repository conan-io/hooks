import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH021(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import copy
            import os
            class AConan(ConanFile):
                name = "name"
                url = "fake_url.com"
                license = "fake_license"
                description = "whatever"
                homepage = "homepage.com"
                topics = ("fake_topic", "another_fake_topic")
                exports_sources = "header.h"
                {placeholder}

                def package(self):
                    copy(self, pattern="*", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH021, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_cmake_minimum_version(self):
        cmake = """project(test)
        """
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="exports_sources = 'CMakeLists.txt'"))
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CMAKEFILE LINT (KB-H021)] The CMake file" in output
        assert "must contain a minimum version declared at the beginning" in output

    def test_regular_cmake(self):
        cmake = textwrap.dedent("""
        cmake_minimum_required(VERSION 3.15)
        project(test)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output

    def test_outdated_cmake(self):
        cmake = textwrap.dedent("""
        cmake_minimum_required(VERSION 2.8)
        project(test)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CMAKEFILE LINT (KB-H021)] The" in output
        assert "requires CMake 3.15 at least" in output

    def test_cmake_minimum_version_with_comment(self):
        cmake = textwrap.dedent("""
        # foobar.cmake
        cmake_minimum_required(VERSION 3.15)
        project(test)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output

    def test_cmake_minimum_version(self):
        cmake = textwrap.dedent("""

        cmake_minimum_required(VERSION 3.15)
        project(test)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output

    def test_cmake_minimum_version_test_package(self):
        conanfile = self.conanfile.format(placeholder="exports_sources = \"CMakeLists.txt\"")
        conanfile_tp = textwrap.dedent("""\
        from conan import ConanFile
        from conan.tools.cmake import CMake
        class TestConan(ConanFile):
            settings = "os", "arch"

            def build(self):
                cmake = CMake(self)

            def test(self):
                self.run("echo bar")
        """)
        cmake = """cmake_minimum_required(VERSION 3.15)
        project(test)
        """
        save(self, 'conanfile.py', content=conanfile)
        save(self, 'CMakeLists.txt', content=cmake)
        save(self, 'test_package/CMakeLists.txt', content=cmake)
        save(self, 'test_package/conanfile.py', content=conanfile_tp)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output
        # validate residual cmake files in test_package/build
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output
        assert "ERROR: [CMAKEFILE LINT (KB-H021)]" not in output

    def test_cmake_minimum_required_upper_case(self):
        cmake = textwrap.dedent("""CMAKE_MINIMUM_REQUIRED (VERSION 3.15)
        project(test)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output

    def test_cmake_minimum_required_lower_case(self):
        cmake = textwrap.dedent("""cmake_minimum_required(VERSION 3.15)
        project(test)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output
        assert "ERROR: [CMAKEFILE LINT (KB-H021)]" not in output

    def test_cmake_minimum_required_with_project_first(self):
        cmake = textwrap.dedent("""project(test)
        cmake_minimum_required(VERSION 3.15)
        """)
        save(self, 'CMakeLists.txt', content=cmake)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[CMAKEFILE LINT (KB-H021)] OK" in output