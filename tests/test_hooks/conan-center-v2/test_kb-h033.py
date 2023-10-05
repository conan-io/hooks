import os
import textwrap
import shutil
import platform
from parameterized import parameterized
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH033(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                from conan import ConanFile
                from conan.tools.cmake import CMake, cmake_layout

                class FooConan(ConanFile):
                    name = "foo"
                    url = "fake_url.com"
                    license = "fake_license"
                    description = "whatever"
                    homepage = "homepage.com"
                    topics = ("fake_topic", "another_fake_topic")

                    settings = "os", "arch", "compiler", "build_type"
                    options = {"shared": [True, False], "fPIC": [True, False]}
                    default_options = {"shared": False, "fPIC": True}

                    exports_sources = "CMakeLists.txt", "foo.h", "foo.c"
                    generators = "CMakeToolchain"

                    def config_options(self):
                        if self.settings.os == "Windows":
                            del self.options.fPIC

                    def configure(self):
                        if self.options.shared:
                            self.options.rm_safe("fPIC")
                        self.settings.rm_safe("compiler.cppstd")
                        self.settings.rm_safe("compiler.libcxx")

                    def layout(self):
                        cmake_layout(self)

                    def build(self):
                        cmake = CMake(self)
                        cmake.configure()
                        cmake.build()

                    def package(self):
                        cmake = CMake(self)
                        cmake.install()

                    def package_info(self):
                        self.cpp_info.libs = ["foo"]
            """)

    foo_h = textwrap.dedent("""\
                #pragma once
                #include "foo_export.h"
                FOO_API int foo_test();
            """)

    foo_c = textwrap.dedent("""\
                #include "foo.h"
                int foo_test() {return 1;}
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH033, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def setup_method(self, method):
        self.conan(['profile', 'detect', '--force'])

    @staticmethod
    def cmakelists(install_name_dir="@rpath"):
        if install_name_dir == "@rpath":
            cmake_install_name_dir = ""
        else:
            cmake_install_name_dir = f"set(CMAKE_INSTALL_NAME_DIR \"{install_name_dir}\")"

        return textwrap.dedent(f"""\
                cmake_minimum_required(VERSION 3.15)
                project(test_relocatable LANGUAGES C)

                include(GenerateExportHeader)
                include(GNUInstallDirs)

                {cmake_install_name_dir}

                add_library(foo foo.c)
                generate_export_header(foo EXPORT_MACRO_NAME FOO_API)
                set_target_properties(foo PROPERTIES C_VISIBILITY_PRESET hidden)
                target_include_directories(foo PUBLIC
                    $<BUILD_INTERFACE:${{PROJECT_SOURCE_DIR}}>
                    $<BUILD_INTERFACE:${{PROJECT_BINARY_DIR}}>
                )

                install(FILES ${{PROJECT_SOURCE_DIR}}/foo.h ${{PROJECT_BINARY_DIR}}/foo_export.h
                        DESTINATION ${{CMAKE_INSTALL_INCLUDEDIR}})
                install(TARGETS foo
                        RUNTIME DESTINATION ${{CMAKE_INSTALL_BINDIR}}
                        ARCHIVE DESTINATION ${{CMAKE_INSTALL_LIBDIR}}
                        LIBRARY DESTINATION ${{CMAKE_INSTALL_LIBDIR}})
            """)

    @parameterized.expand([
        (False, "@rpath"),
        (False, ""),
        (False, "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}"),
        (True, "@rpath"),
        (True, ""),
        (True, "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}"),
    ])
    def test_relocatable(self, shared, install_name_dir):
        save(self, "conanfile.py", content=self.conanfile)
        save(self, "CMakeLists.txt", content=self.cmakelists(install_name_dir))
        save(self, "foo.h", content=self.foo_h)
        save(self, "foo.c", content=self.foo_c)
        output = self.conan(["create", "conanfile.py", "--name=foo", "--version=0.1.0", "-o", f"foo/0.1.0:shared={shared}"])
        if platform.system() == "Darwin" and shared and install_name_dir != "@rpath":
            assert "WARN: [APPLE RELOCATABLE SHARED LIBS (KB-H033)] install_name dir of these shared libs is not @rpath: libfoo.dylib" in output
        else:
            assert "[APPLE RELOCATABLE SHARED LIBS (KB-H033)] OK" in output