import os
import platform
import textwrap

from conans import tools
from conans.client.command import ERROR_INVALID_CONFIGURATION, SUCCESS, ERROR_GENERAL

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
            settings = "os", "compiler", "arch", "build_type"

            def package(self):
                self.copy("*", dst="include")

            def package_id(self):
                self.info.header_only()
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
        self.assertIn("[NOT ALLOWED ATTRIBUTES (KB-H039)] OK", output)

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
        self.assertIn("[NOT ALLOWED ATTRIBUTES (KB-H039)] OK", output)

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
            "WARN: [RECIPE METADATA (KB-H003)] Conanfile doesn't have 'topics' attribute."
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
                      "minimum version declared (e.g. cmake_minimum_required(VERSION 3.1.2))" % path,
                      output)

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
        self.assertNotIn("ERROR [CMAKE MINIMUM VERSION (KB-H028)]", output)

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
        self.assertNotIn("ERROR [CMAKE MINIMUM VERSION (KB-H028)]", output)

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

    def test_no_scm(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            {}
            def configure(self):
                pass
        """)

        tools.save('conanfile.py', content=conanfile.replace("{}", "revision_mode = 'scm'"))
        output = self.conan(['export', '.', 'name/version@user/test'], expected_return_code=ERROR_GENERAL)
        self.assertIn("ERROR: [NOT ALLOWED ATTRIBUTES (KB-H039)] Conanfile should not contain attributes related to revision. Remove 'revision_mode'.", output)

        scm = textwrap.dedent("""\
        scm = {"type": "git",
               "subfolder": "hello",
               "url": "auto",
               "revision": "auto"}
        """)
        tools.save('conanfile.py', content=conanfile.replace("{}", scm))
        output = self.conan(['export', '.', 'name/version@user/test'], expected_return_code=ERROR_GENERAL)
        self.assertIn("ERROR: [NOT ALLOWED ATTRIBUTES (KB-H039)] Conanfile should not contain attributes related to revision. Remove 'scm'.", output)
