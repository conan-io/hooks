# coding=utf-8

import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ConanCenterTests(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
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
            exports_sources = "header.h"
            settings = "os", "compiler", "arch", "build_type"

            def package(self):
                self.copy("*", dst="include")

            def package_id(self):
                self.info.header_only()
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
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertNotIn("[PACKAGE LICENSE] OK", output)

    def test_conanfile(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA] OK", output)
        self.assertIn("[HEADER ONLY] OK", output)
        self.assertIn("[NO COPY SOURCE] OK", output)
        self.assertIn("[FPIC OPTION] OK", output)
        self.assertIn("[FPIC MANAGEMENT] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES] OK", output)
        self.assertIn("[LIBCXX] OK", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION] Empty package", output)
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)

    def test_conanfile_header_only(self):
        tools.save('conanfile.py', content=self.conanfile_header_only)
        tools.save('header.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA] OK", output)
        self.assertIn("[HEADER ONLY] OK", output)
        self.assertIn("[NO COPY SOURCE] This recipe seems to be for a header only", output)
        self.assertIn("[FPIC OPTION] OK", output)
        self.assertIn("[FPIC MANAGEMENT] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES] OK", output)
        self.assertIn("[LIBCXX] OK", output)
        self.assertIn("[MATCHING CONFIGURATION] OK", output)
        self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)

    def test_conanfile_header_only_with_settings(self):
        tools.save('conanfile.py', content=self.conanfile_header_only_with_settings)
        tools.save('header.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA] OK", output)
        self.assertIn("[HEADER ONLY] OK", output)
        self.assertIn("[NO COPY SOURCE] OK", output)
        self.assertIn("[FPIC OPTION] OK", output)
        self.assertIn("[FPIC MANAGEMENT] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES] OK", output)
        self.assertIn("[LIBCXX] OK", output)
        self.assertIn("[MATCHING CONFIGURATION] OK", output)
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)

    def test_conanfile_installer(self):
        tools.save('conanfile.py', content=self.conanfile_installer)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA] OK", output)
        self.assertIn("[HEADER ONLY] OK", output)
        self.assertIn("[NO COPY SOURCE] OK", output)
        self.assertIn("[FPIC OPTION] OK", output)
        self.assertIn("[FPIC MANAGEMENT] 'fPIC' option not found", output)
        self.assertIn("[VERSION RANGES] OK", output)
        self.assertIn("[LIBCXX] OK", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION] Empty package", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION] Packaged artifacts does not match",
                      output)
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)
