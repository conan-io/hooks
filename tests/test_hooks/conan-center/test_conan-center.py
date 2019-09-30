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
        self.assertIn("[VERSION ATTRIBUTE (KB-H026)] OK", output)

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
        self.assertIn("[VERSION ATTRIBUTE (KB-H026)] OK", output)

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
        self.assertIn("[VERSION ATTRIBUTE (KB-H026)] OK", output)

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
        self.assertIn("[VERSION ATTRIBUTE (KB-H026)] OK", output)

    def test_version_folder_name(self):
        tools.save('all/conanfile.py', content=self.conanfile)
        output = self.conan(['create', 'all', 'name/version@user/test'])
        self.assertIn("ERROR: [VERSION ATTRIBUTE (KB-H026)] The recipe folder `all` is generic, " \
                      "but your recipe contains the attribute version. Remove the attribute " \
                      "`version` from the recipe", output)
