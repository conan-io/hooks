import os
import platform
import textwrap

from parameterized import parameterized

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestAppleRelocatableSharedLibs(ConanClientTestCase):
    def _get_environ(self, **kwargs):
        kwargs = super(TestAppleRelocatableSharedLibs, self)._get_environ(**kwargs)
        kwargs.update({
            "CONAN_HOOKS": os.path.join(os.path.dirname(__file__), os.pardir,
                           os.pardir, os.pardir, "hooks", "conan-center")
        })
        return kwargs

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
        tools.save("conanfile.py", content=self.conanfile)
        tools.save("CMakeLists.txt", content=self.cmakelists(install_name_dir))
        tools.save("foo.h", content=self.foo_h)
        tools.save("foo.c", content=self.foo_c)
        output = self.conan(["create", ".", "foo/1.0@user/test", "-o", f"foo:shared={shared}"])
        if platform.system() == "Darwin" and shared and install_name_dir != "@rpath":
            self.assertIn("ERROR: [APPLE RELOCATABLE SHARED LIBS (KB-H077)] install_name dir of these shared libs is not @rpath: libfoo.dylib", output)
        else:
            self.assertIn("[APPLE RELOCATABLE SHARED LIBS (KB-H077)] OK", output)
