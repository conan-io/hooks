# coding=utf-8
import os
import platform
import textwrap
import pytest
import six

from conans import tools
from conans.client.command import ERROR_INVALID_CONFIGURATION, SUCCESS
from conans.tools import Version
from conans import __version__ as conan_version

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ConanCenterTests(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            homepage = "homepage.com"
            topics = ("fake_topic", "another_fake_topic")
            exports_sources = "header.h"
            {placeholder}

            def package(self):
                self.copy("*", dst="include")
        """)
    conanfile_header_only_with_settings = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            homepage = "homepage.com"
            exports_sources = "header.h"
            topics = ("one", "two")
            settings = "os", "compiler", "arch", "build_type"

            def package(self):
                self.copy("*", dst="include")

            def package_id(self):
                self.info.header_only()
        """)
    conanfile_settings_clear_with_settings = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            homepage = "homepage.com"
            topics = ("one", "two")
            exports_sources = "header.h"
            settings = "os", "compiler", "arch", "build_type"

            def package(self):
                self.copy("*", dst="include")

            def package_id(self):
                self.info.settings.clear()
        """)
    conanfile_fpic = textwrap.dedent("""\
            from conans import ConanFile

            class Fpic(ConanFile):
                url = "fake_url.com"
                license = "fake_license"
                description = "whatever"
                settings = "os", "arch", "compiler", "build_type"
                options = {'fPIC': [True, False]}
                default_options = {'fPIC': True}
            """)
    conanfile_header_only = conanfile_base.format(placeholder='')
    conanfile_installer = conanfile_base.format(placeholder='settings = "os_build"')
    conanfile = conanfile_base.format(placeholder='settings = "os"')

    def _get_environ(self, **kwargs):
        kwargs = super(ConanCenterTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_no_duplicated_messages(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("ERROR: [PACKAGE LICENSE (KB-H012)] No 'licenses' folder found in package", output)
        self.assertNotIn("[PACKAGE LICENSE (KB-H012)] OK", output)

    def test_conanfile(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA (KB-H003)] OK", output)
        self.assertIn("[HEADER_ONLY, NO COPY SOURCE (KB-H005)] OK", output)
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        self.assertIn("[FPIC MANAGEMENT (KB-H007)] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES (KB-H008)] OK", output)
        self.assertIn("[LIBCXX MANAGEMENT (KB-H011)] OK", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION (KB-H014)] Empty package", output)
        self.assertIn("ERROR: [PACKAGE LICENSE (KB-H012)] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
        self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
        self.assertIn("[EXPORT LICENSE (KB-H023)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE FOLDER (KB-H024)] There is no 'test_package' for this "
                      "recipe", output)
        self.assertIn("[META LINES (KB-H025)] OK", output)
        self.assertIn("ERROR: [CONAN CENTER INDEX URL (KB-H027)] The attribute 'url' should " \
                      "point to: https://github.com/conan-io/conan-center-index", output)
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        self.assertIn("[SYSTEM REQUIREMENTS (KB-H032)] OK", output)

    def test_conanfile_header_only(self):
        tools.save('conanfile.py', content=self.conanfile_header_only)
        tools.save('header.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA (KB-H003)] OK", output)
        self.assertIn("[HEADER_ONLY, NO COPY SOURCE (KB-H005)] This recipe is a header only library", output)
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        self.assertIn("[FPIC MANAGEMENT (KB-H007)] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES (KB-H008)] OK", output)
        self.assertIn("[LIBCXX MANAGEMENT (KB-H011)] OK", output)
        self.assertIn("[MATCHING CONFIGURATION (KB-H014)] OK", output)
        self.assertNotIn("ERROR: [MATCHING CONFIGURATION (KB-H014)]", output)
        self.assertIn("ERROR: [PACKAGE LICENSE (KB-H012)] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
        self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
        self.assertIn("[EXPORT LICENSE (KB-H023)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE FOLDER (KB-H024)] There is no 'test_package' for this "
                      "recipe", output)
        self.assertIn("[META LINES (KB-H025)] OK", output)
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        self.assertIn("[SYSTEM REQUIREMENTS (KB-H032)] OK", output)

    def test_conanfile_header_only_with_settings(self):
        tools.save('conanfile.py', content=self.conanfile_header_only_with_settings)
        tools.save('header.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA (KB-H003)] OK", output)
        self.assertIn("[HEADER_ONLY, NO COPY SOURCE (KB-H005)] OK", output)
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        self.assertIn("[FPIC MANAGEMENT (KB-H007)] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES (KB-H008)] OK", output)
        self.assertIn("[LIBCXX MANAGEMENT (KB-H011)] OK", output)
        self.assertIn("[MATCHING CONFIGURATION (KB-H014)] OK", output)
        self.assertIn("ERROR: [PACKAGE LICENSE (KB-H012)] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
        self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
        self.assertIn("[EXPORT LICENSE (KB-H023)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE FOLDER (KB-H024)] There is no 'test_package' for this "
                      "recipe", output)
        self.assertIn("[META LINES (KB-H025)] OK", output)
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        self.assertIn("[SYSTEM REQUIREMENTS (KB-H032)] OK", output)

    def test_conanfile_settings_clear_with_settings(self):
        tools.save('conanfile.py', content=self.conanfile_settings_clear_with_settings)
        tools.save('header.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA (KB-H003)] OK", output)
        self.assertIn("[HEADER_ONLY, NO COPY SOURCE (KB-H005)] OK", output)
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        self.assertIn("[FPIC MANAGEMENT (KB-H007)] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES (KB-H008)] OK", output)
        self.assertIn("[LIBCXX MANAGEMENT (KB-H011)] OK", output)
        self.assertIn("[MATCHING CONFIGURATION (KB-H014)] OK", output)
        self.assertIn("ERROR: [PACKAGE LICENSE (KB-H012)] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
        self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
        self.assertIn("[EXPORT LICENSE (KB-H023)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE FOLDER (KB-H024)] There is no 'test_package' for this "
                      "recipe", output)
        self.assertIn("[META LINES (KB-H025)] OK", output)
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        self.assertIn("[SYSTEM REQUIREMENTS (KB-H032)] OK", output)

    def test_conanfile_installer(self):
        tools.save('conanfile.py', content=self.conanfile_installer)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA (KB-H003)] OK", output)
        self.assertIn("[HEADER_ONLY, NO COPY SOURCE (KB-H005)] OK", output)
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        self.assertIn("[FPIC MANAGEMENT (KB-H007)] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES (KB-H008)] OK", output)
        self.assertIn("[LIBCXX MANAGEMENT (KB-H011)] OK", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION (KB-H014)] Empty package", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION (KB-H014)] Packaged artifacts does not match",
                      output)
        self.assertIn("ERROR: [PACKAGE LICENSE (KB-H012)] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT (KB-H013)] OK", output)
        self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE FOLDER (KB-H024)] There is no 'test_package' for this "
                      "recipe", output)
        self.assertIn("[META LINES (KB-H025)] OK", output)
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)

    def test_shebang(self):
        conanfile = textwrap.dedent("""\
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        from conans import ConanFile, tools
        import os

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            exports_sources = "header.h"

            def package(self):
                tools.save(os.path.join(self.package_folder, "__init__.py"),
                           content="#!/usr/bin/env python")
                self.copy("*", dst="include")

        # vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [META LINES (KB-H025)] PEP 263 (encoding) is not allowed in the " \
                      "conanfile. Remove the line 2", output)
        self.assertIn("ERROR: [META LINES (KB-H025)] vim editor configuration detected in your " \
                      "recipe. Remove the line 17", output)
        self.assertIn("ERROR: [META LINES (KB-H025)] Shebang (#!) detected in your recipe. " \
                      "Remove the line 1", output)

    def test_run_environment_test_package(self):
        conanfile_tp = textwrap.dedent("""\
        from conans import ConanFile, RunEnvironment, tools

        class TestConan(ConanFile):
            settings = "os", "arch"

            def test(self):
                env_build = RunEnvironment(self)
                with tools.environment_append(env_build.vars):
                    self.run("echo bar")
        """)
        tools.save('test_package/conanfile.py', content=conanfile_tp)
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[TEST PACKAGE FOLDER (KB-H024)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE - RUN ENVIRONMENT (KB-H029)] The 'RunEnvironment()' "
                      "build helper is no longer needed. It has been integrated into the "
                      "self.run(..., run_environment=True)", output)

        conanfile_tp = textwrap.dedent("""\
        from conans import ConanFile, tools

        class TestConan(ConanFile):
            settings = "os", "arch"

            def test(self):
                self.run("echo bar", run_environment=True)
        """)

        tools.save('test_package/conanfile.py', content=conanfile_tp)
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[TEST PACKAGE FOLDER (KB-H024)] OK", output)
        self.assertIn("[TEST PACKAGE - RUN ENVIRONMENT (KB-H029)] OK", output)
        self.assertIn("[EXPORT LICENSE (KB-H023)] OK", output)
        self.assertIn("[TEST PACKAGE - NO IMPORTS() (KB-H034)] OK", output)

        conanfile_tp = textwrap.dedent("""\
        from conans import ConanFile, tools
        from conans import ConanFile, CMake, RunEnvironment

        class TestConan(ConanFile):
            settings = "os", "arch"

            def build(self):
                with tools.environment_append(RunEnvironment(self).vars):
                    self.output.info("foobar")

            def test(self):
                self.run("echo bar", run_environment=True)
        """)

        tools.save('test_package/conanfile.py', content=conanfile_tp)
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[TEST PACKAGE FOLDER (KB-H024)] OK", output)
        self.assertIn("[TEST PACKAGE - RUN ENVIRONMENT (KB-H029)] OK", output)
        self.assertIn("[EXPORT LICENSE (KB-H023)] OK", output)
        self.assertIn("[TEST PACKAGE - NO IMPORTS() (KB-H034)] OK", output)

    def test_exports_licenses(self):
        tools.save('conanfile.py',
                   content=self.conanfile_base.format(placeholder='exports = "LICENSE"'))
        output = self.conan(['create', '.', 'name/version@name/test'])
        self.assertIn("ERROR: [EXPORT LICENSE (KB-H023)] This recipe is exporting a license file." \
                      " Remove LICENSE from `exports`", output)

        tools.save('conanfile.py',
                   content=self.conanfile_base.format(placeholder='exports_sources = "LICENSE"'))
        output = self.conan(['create', '.', 'name/version@name/test'])
        self.assertIn("ERROR: [EXPORT LICENSE (KB-H023)] This recipe is exporting a license file." \
                      " Remove LICENSE from `exports_sources`", output)

        tools.save('conanfile.py',
                   content=self.conanfile_base.format(placeholder='exports = ["foobar", "COPYING.md"]'))
        output = self.conan(['create', '.', 'name/version@name/test'])
        self.assertIn("ERROR: [EXPORT LICENSE (KB-H023)] This recipe is exporting a license file." \
                      " Remove COPYING.md from `exports`", output)

    def test_fpic_remove(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class LinuxOnly(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            settings = "os", "arch", "compiler", "build_type"
            options = {"fPIC": [True, False], "shared": [True, False]}
            default_options = {"fPIC": True, "shared": False}
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'package/version@conan/test'])
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        if tools.os_info.is_windows:
            self.assertIn("ERROR: [FPIC MANAGEMENT (KB-H007)] 'fPIC' option not managed " \
                          "correctly. Please remove it for Windows " \
                          "configurations: del self.options.fpic", output)
        else:
            self.assertIn("[FPIC MANAGEMENT (KB-H007)] OK. 'fPIC' option found and apparently " \
                        "well managed", output)

    def test_fpic_remove_windows(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class Conan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            settings = "os", "arch", "compiler", "build_type"
            options = {"fPIC": [True, False], "shared": [True, False]}
            default_options = {"fPIC": True, "shared": False}

            def config_options(self):
                if self.settings.os == "Windows":
                    del self.options.fPIC
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'package/version@conan/test'])
        self.assertIn("[FPIC OPTION (KB-H006)] OK", output)
        if platform.system() == "Windows":
            self.assertIn("[FPIC MANAGEMENT (KB-H007)] 'fPIC' option not found", output)
        else:
            self.assertIn("[FPIC MANAGEMENT (KB-H007)] OK. 'fPIC' option found and apparently well "
                          "managed", output)
        self.assertIn("[FPIC MANAGEMENT (KB-H007)] OK", output)

    def test_fpic_remove_windows_configuration(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        from conans.errors import ConanInvalidConfiguration

        class Conan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            settings = "os", "arch", "compiler", "build_type"
            options = {"fPIC": [True, False], "shared": [True, False]}
            default_options = {"fPIC": True, "shared": False}

            def configure(self):
                if self.settings.os == "Windows":
                    raise ConanInvalidConfiguration("Windows not supported")
        """)
        tools.save('conanfile.py', content=conanfile)
        if platform.system() == "Windows":
            expected_return_code = ERROR_INVALID_CONFIGURATION
        else:
            expected_return_code = SUCCESS
        output = self.conan(['create', '.', 'package/version@conan/test'], expected_return_code)
        if platform.system() == "Windows":
            self.assertNotIn("[FPIC MANAGEMENT (KB-H007)] OK", output)
        else:
            self.assertIn("[FPIC MANAGEMENT (KB-H007)] OK. 'fPIC' option found and apparently well "
                          "managed", output)

    def test_conanfile_cppstd(self):
        content = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            exports_sources = "header.h", "test.c"
            settings = "os", "compiler", "arch", "build_type"
            def configure(self):
                {configure}
            def package(self):
                self.copy("*", dst="include")
        """)

        tools.save('test.c', content="#define FOO 1")
        tools.save('conanfile.py', content=content.format(
                   configure="pass"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [LIBCXX MANAGEMENT (KB-H011)] Can't detect C++ source files but " \
                      "recipe does not remove 'self.settings.compiler.libcxx'", output)
        self.assertIn("ERROR: [CPPSTD MANAGEMENT (KB-H022)] Can't detect C++ source files but " \
                      "recipe does not remove 'self.settings.compiler.cppstd'", output)

        tools.save('conanfile.py', content=content.format(configure="""
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd"""))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[LIBCXX MANAGEMENT (KB-H011)] OK", output)
        self.assertIn("[CPPSTD MANAGEMENT (KB-H022)] OK", output)

    def test_missing_attributes(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            pass
        """)
        bad_recipe_output = [
            "ERROR: [RECIPE METADATA (KB-H003)] Conanfile doesn't have 'url' attribute.",
            "ERROR: [RECIPE METADATA (KB-H003)] Conanfile doesn't have 'license' attribute.",
            "ERROR: [RECIPE METADATA (KB-H003)] Conanfile doesn't have 'description' attribute.",
            "ERROR: [RECIPE METADATA (KB-H003)] Conanfile doesn't have 'homepage' attribute.",
            "ERROR: [RECIPE METADATA (KB-H003)] Conanfile doesn't have 'topics' attribute."
        ]

        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        for msg in bad_recipe_output:
            self.assertIn(msg, output)
        self.assertNotIn("[RECIPE METADATA (KB-H003)] OK", output)

        tools.save('conanfile.py', content=self.conanfile_base.format(placeholder=''))
        output = self.conan(['create', '.', 'name/version@user/test'])
        for msg in bad_recipe_output:
            self.assertNotIn(msg, output)
        self.assertIn("[RECIPE METADATA (KB-H003)] OK", output)

    def test_cci_url(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            url = "https://github.com/conan-io/conan-center-index"
            license = "fake_license"
            description = "whatever"
            exports_sources = "header.h"
            def package(self):
                self.copy("*", dst="include")
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[CONAN CENTER INDEX URL (KB-H027)] OK", output)

    def test_cmake_minimum_version(self):
        conanfile = self.conanfile_base.format(placeholder="exports_sources = \"CMakeLists.txt\"")
        cmake = """project(test)
        """
        tools.save('conanfile.py', content=conanfile)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        path = os.path.join(".", "CMakeLists.txt")
        self.assertIn("ERROR: [CMAKE MINIMUM VERSION (KB-H028)] The CMake file '%s' must contain a "
                      "minimum version declared at the beginning "
                      "(e.g. cmake_minimum_required(VERSION 3.1.2))" % path,
                      output)

        cmake = textwrap.dedent("""
        # foobar.cmake
        cmake_minimum_required(VERSION 2.8)
        project(test)
        """)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)

        cmake = textwrap.dedent("""

        cmake_minimum_required(VERSION 2.8)
        project(test)
        """)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)

    def test_cmake_minimum_version_test_package(self):
        conanfile = self.conanfile_base.format(placeholder="exports_sources = \"CMakeLists.txt\"")
        conanfile_tp = textwrap.dedent("""\
        from conans import ConanFile, tools, CMake

        class TestConan(ConanFile):
            settings = "os", "arch"

            def build(self):
                cmake = CMake(self)

            def test(self):
                self.run("echo bar", run_environment=True)
        """)
        cmake = """cmake_minimum_required(VERSION 2.8.11)
        project(test)
        """
        tools.save('conanfile.py', content=conanfile)
        tools.save('CMakeLists.txt', content=cmake)
        tools.save('test_package/CMakeLists.txt', content=cmake)
        tools.save('test_package/conanfile.py', content=conanfile_tp)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        # validate residual cmake files in test_package/build
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        self.assertNotIn("ERROR: [CMAKE MINIMUM VERSION (KB-H028)]", output)

        cmake = textwrap.dedent("""CMAKE_MINIMUM_REQUIRED (VERSION 2.8.11)
        project(test)
        """)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)

        cmake = textwrap.dedent("""cmake_minimum_required(VERSION 2.8.11)
        project(test)
        """)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)
        self.assertNotIn("ERROR: [CMAKE MINIMUM VERSION (KB-H028)]", output)

        cmake = textwrap.dedent("""project(test)
        cmake_minimum_required(VERSION 2.8.11)
        """)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE MINIMUM VERSION (KB-H028)]", output)
        self.assertNotIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)

        cmake = """cmake_minimum_required(VERSION 2.8.11)
        project(test)
        """
        tools.save('CMakeLists.txt', content=cmake)
        cmake = textwrap.dedent("""project(test)
        cmake_minimum_required(VERSION 2.8.11)
        """)
        tools.save('test_package/CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE MINIMUM VERSION (KB-H028)]", output)
        self.assertNotIn("[CMAKE MINIMUM VERSION (KB-H028)] OK", output)

    def test_system_requirements(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        from conans.tools import SystemPackageTool
        class SystemReqConan(ConanFile):
            url = "https://github.com/conan-io/conan-center-index"
            license = "fake_license"
            description = "whatever"
            def system_requirements(self):
                installer = SystemPackageTool()
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[SYSTEM REQUIREMENTS (KB-H032)] OK", output)

        conanfile += "        installer.install([])"
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [SYSTEM REQUIREMENTS (KB-H032)] The method " \
                      "'SystemPackageTool.install' is not allowed in the recipe.", output)

        conanfile = conanfile.replace("installer.install([])", "SystemPackageTool().install([])")
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [SYSTEM REQUIREMENTS (KB-H032)] The method " \
                      "'SystemPackageTool.install' is not allowed in the recipe.", output)

        output = self.conan(['create', '.', 'libusb/version@user/test'])
        self.assertIn("[SYSTEM REQUIREMENTS (KB-H032)] 'libusb' is part of the allowlist.", output)
        self.assertNotIn("ERROR: [SYSTEM REQUIREMENTS (KB-H032)]", output)

    def test_imports_not_allowed(self):
        conanfile_tp = textwrap.dedent("""\
        from conans import ConanFile, tools

        class TestConan(ConanFile):
            settings = "os", "arch"

            def imports(self):
                self.copy("*.dll", "", "bin")
                self.copy("*.dylib", "", "lib")

            def test(self):
                self.run("echo bar", run_environment=True)
        """)

        tools.save('test_package/conanfile.py', content=conanfile_tp)
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[TEST PACKAGE FOLDER (KB-H024)] OK", output)
        self.assertIn("[TEST PACKAGE - RUN ENVIRONMENT (KB-H029)] OK", output)
        self.assertIn("ERROR: [TEST PACKAGE - NO IMPORTS() (KB-H034)] The method `imports` is not " \
                      "allowed in test_package/conanfile.py", output)

    def test_requirements_add(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
                pass
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[NO REQUIRES.ADD() (KB-H044)] OK", output)

        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
                def requirements(self):
                    {}
        """)

        tools.save('conanfile.py',
                   content=conanfile.replace("{}", 'self.requires("name/version@user/test")'))
        output = self.conan(['create', '.', 'foo/version@user/test'])
        self.assertIn("[NO REQUIRES.ADD() (KB-H044)] OK", output)

        tools.save('conanfile.py',
                   content=conanfile.replace("{}", 'self.requires.add("name/version@user/test")'))
        output = self.conan(['create', '.', 'foo/version@user/test'])
        self.assertIn("[NO REQUIRES.ADD() (KB-H044)] The method 'self.requires.add()' is not " \
                      "allowed. Use 'self.requires()' instead.", output)

        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
                def build_requirements(self):
                    {}
        """)

        tools.save('conanfile.py',
                   content=conanfile.replace("{}", 'self.build_requires("name/version@user/test")'))
        output = self.conan(['create', '.', 'foo/version@user/test'])
        self.assertIn("[NO REQUIRES.ADD() (KB-H044)] OK", output)

        # Conan >= 1.23 requires "context" parameter for build_requires.add()
        if Version(conan_version) < "1.23":
            tools.save('conanfile.py',
                    content=conanfile.replace("{}", 'self.build_requires.add("name/version@user/test")'))
            output = self.conan(['create', '.', 'foo/version@user/test'])
            self.assertIn("[NO REQUIRES.ADD() (KB-H044)] The method 'self.build_requires.add()' is not " \
                        "allowed. Use 'self.build_requires()' instead.", output)

    def test_no_author(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            {}
            def configure(self):
                pass
        """)
        tools.save('conanfile.py', content=conanfile.replace("{}", ""))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[NO AUTHOR (KB-H037)] OK", output)

        tools.save('conanfile.py', content=conanfile.replace("{}", "author = 'foobar'"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn('ERROR: [NO AUTHOR (KB-H037)] Conanfile should not contain author. '
                      'Remove \'author = "foobar"\'', output)

        tools.save('conanfile.py', content=conanfile.replace("{}", "author = ('foo', 'bar')"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn('ERROR: [NO AUTHOR (KB-H037)] Conanfile should not contain author. '
                      'Remove \'author = (\'foo\', \'bar\')', output)

    @pytest.mark.skipif(Version(conan_version) < "1.21", reason="requires Conan 1.21 or higher")
    def test_no_target_name(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            def package_info(self):
                {}

        """)
        pkg_config = 'self.cpp_info.names["pkg_config"] = "foolib"'
        regular = 'self.cpp_info.name = "Foo"'
        cmake = 'self.cpp_info.names["cmake"] = "Foo"'
        cmake_multi = 'self.cpp_info.names["cmake_multi"] = "Foo"'
        cmake_find = 'self.cpp_info.names["cmake_find_package"] = "Foo"'
        cmake_find_multi = 'self.cpp_info.names["cmake_find_package_multi"] = "Foo"'

        tools.save('conanfile.py', content=conanfile.replace("{}", regular))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO TARGET NAME (KB-H040)] "
                      "CCI uses the name of the package for cmake generator."
                      " Use 'cpp_info.names' instead.", output)

        for line, gen in [(cmake, "cmake"), (cmake_multi, "cmake_multi")]:
            tools.save('conanfile.py', content=conanfile.replace("{}", line))
            output = self.conan(['create', '.', 'name/version@user/test'])
            self.assertIn("ERROR: [NO TARGET NAME (KB-H040)] CCI uses the name of the package for "
                          "{0} generator. Conanfile should not contain "
                          "'self.cpp_info.names['{0}']'. "
                          " Use 'cmake_find_package' and 'cmake_find_package_multi' instead.".format(gen), output)

        for it in [pkg_config, cmake_find, cmake_find_multi]:
            tools.save('conanfile.py', content=conanfile.replace("{}", it))
            output = self.conan(['create', '.', 'name/version@user/test'])
            self.assertIn("[NO TARGET NAME (KB-H040)] OK", output)

    def test_cmake_verbose_makefile(self):
        conanfile = self.conanfile_base.format(placeholder="exports_sources = \"CMakeLists.txt\"")

        cmake = textwrap.dedent("""
                cmake_minimum_required(VERSION 2.8.11)
                project(test)
                """)
        tools.save('conanfile.py', content=conanfile)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE VERBOSE MAKEFILE (KB-H046)] OK", output)

        cmake = """cmake_minimum_required(VERSION 2.8.11)
        project(test)

        set(CMAKE_VERBOSE_MAKEFILE ON)
        """
        tools.save('CMakeLists.txt', content=cmake)
        print("CWD: %s" % os.getcwd())
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE VERBOSE MAKEFILE (KB-H046)] The CMake definition "
                      "'set(CMAKE_VERBOSE_MAKEFILE ON)' is not allowed."
                      " Remove it from CMakeLists.txt.", output)

        conanfile_tp = textwrap.dedent("""\
        from conans import ConanFile

        class TestConan(ConanFile):
            settings = "os", "arch"

            def test(self):
                pass
        """)
        tools.save('test_package/conanfile.py', content=conanfile_tp)
        tools.save('test_package/CMakeLists.txt', content=cmake)
        tools.save('CMakeLists.txt', content=cmake.replace("set(CMAKE_VERBOSE_MAKEFILE ON)", ""))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertNotIn("Remove it from CMakeLists.txt", output)
        self.assertIn("ERROR: [CMAKE VERBOSE MAKEFILE (KB-H046)] The CMake definition "
                      "'set(CMAKE_VERBOSE_MAKEFILE ON)' is not allowed."
                      " Remove it from {}."
                      .format(os.path.join("test_package", "CMakeLists.txt")), output)

    @pytest.mark.skipif(six.PY2, reason="Python2 doesn't support utf-8 by default")
    def test_non_ascii_characters(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            {}
            pass
        """)
        tools.save('conanfile.py', content=conanfile.replace("{}", "# Conan, the barbarian"))
        tools.save(os.path.join('test_package', 'conanfile.py'),
                                 content=conanfile.replace("{}", "def test(self): # Conan, the barbarian").replace("pass", "    pass"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[NO ASCII CHARACTERS (KB-H047)] OK", output)

        tools.save('conanfile.py', content=conanfile.replace("{}", "# Conan, o bárbaro"))
        tools.save(os.path.join('test_package', 'conanfile.py'),
                   content=conanfile.replace("{}", "def test(self): # Conan, o bárbaro").replace("pass", "    pass"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO ASCII CHARACTERS (KB-H047)] The file 'conanfile.py' contains a non-ascii character at line (3)." \
                      " Only ASCII characters are allowed, please remove it.", output)
        self.assertIn("ERROR: [NO ASCII CHARACTERS (KB-H047)] The file 'test_package/conanfile.py' contains a non-ascii character at line (3)." \
                      " Only ASCII characters are allowed, please remove it.", output)

    def test_delete_option(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            options = {"foo": [True, False]}

            def config_options(self):
                {}
        """)
        tools.save('conanfile.py', content=conanfile.replace("{}", "del self.options.foo"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[DELETE OPTIONS (KB-H045)] OK", output)

        tools.save('conanfile.py', content=conanfile.replace("{}", 'self.options.remove("foo")'))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [DELETE OPTIONS (KB-H045)] Found 'self.options.remove'."
                      " Replace it by 'del self.options.<opt>'.", output)

    def test_cmake_version_required(self):
        conanfile = self.conanfile_base.format(placeholder="exports_sources = \"CMakeLists.txt\"")
        cmake = textwrap.dedent("""
                cmake_minimum_required(VERSION 2.8.11)
                project(test)
                """)
        tools.save('conanfile.py', content=conanfile)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE VERSION REQUIRED (KB-H048)] OK", output)

        tools.save('test_package/CMakeLists.txt', content=cmake)
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE VERSION REQUIRED (KB-H048)] The test_packages/CMakeLists.txt "
                      "requires CMake 3.1 at least."
                      " Update to 'cmake_minimum_required(VERSION 3.1)'.", output)

        cmake += "set(CMAKE_CXX_STANDARD 11)"
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE VERSION REQUIRED (KB-H048)] The test_packages/CMakeLists.txt "
                      "requires CMake 3.1 at least."
                      " Update to 'cmake_minimum_required(VERSION 3.1)'.", output)

        cmake = textwrap.dedent("""
                cmake_minimum_required(VERSION 3.1)
                project(test)
                set(CMAKE_CXX_STANDARD 11)
                """)
        tools.save('CMakeLists.txt', content=cmake)
        tools.save('test_package/CMakeLists.txt', content=cmake)
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE VERSION REQUIRED (KB-H048)] OK", output)


    def test_cmake_export_all_symbols_version_required(self):
        conanfile = self.conanfile_base.format(placeholder="exports_sources = \"CMakeLists.txt\"")
        cmake = textwrap.dedent("""
                cmake_minimum_required(VERSION 3.4)
                project(test)
                set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
                """)
        tools.save('conanfile.py', content=conanfile)
        tools.save('CMakeLists.txt', content=cmake)
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE EXPORT ALL SYMBOLS (KB-H049)] OK", output)

        tools.save('CMakeLists.txt', content=cmake.replace("3.4", "2.8.12"))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE EXPORT ALL SYMBOLS (KB-H049)] The CMake definition "
                      "WINDOWS_EXPORT_ALL_SYMBOLS requires CMake 3.4 at least. Update to "
                      "'cmake_minimum_required(VERSION 3.4)'.", output)

        tools.save('CMakeLists.txt', content=cmake.replace("3.4", "3"))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [CMAKE EXPORT ALL SYMBOLS (KB-H049)] The CMake definition "
                      "WINDOWS_EXPORT_ALL_SYMBOLS requires CMake 3.4 at least. Update to "
                      "'cmake_minimum_required(VERSION 3.4)'.", output)

        tools.save('CMakeLists.txt', content=cmake.replace("3.4", "3.17"))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[CMAKE EXPORT ALL SYMBOLS (KB-H049)] OK", output)
