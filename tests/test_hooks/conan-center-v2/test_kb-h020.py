import os
import textwrap
import pytest
import shutil
import platform
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH020(ConanClientV2TestCase):
    cmakefile = textwrap.dedent("""\
        cmake_minimum_required(VERSION 3.15)
        project(foobar CXX)
        add_library(foobar SHARED main.cpp)
        target_link_libraries(foobar PUBLIC m)
        install(TARGETS foobar LIBRARY DESTINATION lib)
        """)
    main = textwrap.dedent("""\
        #include <iostream>
        #include <cmath>
        int main() {
            std::cout << "2 floor: " << floor(2) << std::endl;
            std::cout << "2 sqrt: " << sqrt(2) << std::endl;            
            return 0;
        }
        """)
    conanfile = textwrap.dedent("""\
        from conan import ConanFile
        from conan.tools.cmake import cmake_layout, CMake
        class AConan(ConanFile):
            settings = "os", "compiler", "build_type", "arch"
            exports_sources = "CMakeLists.txt", "main.cpp"
            generators = "CMakeToolchain"
            
            def layout(self):
                cmake_layout(self)
            def build(self):
                cmake = CMake(self)
                cmake.configure(build_script_folder=".")
                cmake.build()
            def package(self):
                cmake = CMake(self)
                cmake.install()
            def package_info(self):
                self.cpp_info.libs = ["foobar"]
                if self.settings.os in ["Linux", "FreeBSD"]:
                    self.cpp_info.system_libs = {placeholder}
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH020, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    @pytest.mark.skipif(platform.system() != "Linux", reason="Only for Linux")
    def test_missing_system_libs(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="[]"))
        save(self, 'CMakeLists.txt', content=self.cmakefile)
        save(self, 'main.cpp', content=self.main)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [MISSING SYSTEM LIBS (KB-H020)] Library" in output

    @pytest.mark.skipif(platform.system() != "Linux", reason="Only for Linux")
    def test_math_system_libs(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="['m']"))
        save(self, 'CMakeLists.txt', content=self.cmakefile)
        save(self, 'main.cpp', content=self.main)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[MISSING SYSTEM LIBS (KB-H020)] OK" in output