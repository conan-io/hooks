# coding=utf-8

import os
import textwrap
import platform

from conans import tools
from parameterized import parameterized

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

            def package_id(self):
                self.info.header_only()
        """)
    conanfile_match_conf = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            exports_sources = "file.{extension}"
            {settings}

            def package(self):
                self.copy("*")
    """)
    conanfile_header_only = conanfile_base.format(placeholder='')
    conanfile_installer = conanfile_base.format(placeholder='settings = "os_build"')
    conanfile = conanfile_base.format(placeholder='settings = "os"')

    def _get_environ(self, **kwargs):
        kwargs = super(ConanCenterTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks',
                                                   'conan-center')})
        return kwargs

    def test_no_duplicated_messages(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertNotIn("[PACKAGE LICENSE] OK", output)

    #@parameterized.expand([("lib", "Windows"), ("so", "Darwin"), ("so", "Linux")])
    #def test_matching_configuration(self, extension, system_name):
    #    cf = self.conanfile_match_conf.format(extension=extension,
    #                                          settings="settings = 'os', 'compiler', 'arch', "
    #                                                   "'build_type'")
    #    tools.save('conanfile.py', content=cf)
    #    tools.save('file.%s' % extension, content="")
    #    output = self.conan(['create', '.', 'name/version@jgsogo/test'])
    #    if platform.system() == system_name:
    #        self.assertIn("[MATCHING CONFIGURATION] OK", output)
    #        self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)
    #    else:
    #        self.assertNotIn("[MATCHING CONFIGURATION] OK", output)
    #        self.assertIn("ERROR: [MATCHING CONFIGURATION]", output)

    def test_matching_configuration_header_only_package_id(self):
        cf = self.conanfile_match_conf.format(extension="h",
                                              settings="settings = 'os', 'compiler', 'arch', "
                                                       "'build_type'")
        cf = cf + """
    def package_id(self):
        self.info.header_only()
        """
        tools.save('conanfile.py', content=cf)
        tools.save('file.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[MATCHING CONFIGURATION] OK", output)
        self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)

    def test_matching_configuration_header_only(self):
        cf = self.conanfile_match_conf.format(extension="h",
                                              settings="")
        tools.save('conanfile.py', content=cf)
        tools.save('file.h', content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[MATCHING CONFIGURATION] OK", output)
        self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)

    def test_matching_configuration_empty(self):
        cf = self.conanfile_match_conf.format(extension="",
                                              settings="settings = 'os', 'compiler', 'arch', "
                                                       "'build_type'")
        tools.save('conanfile.py', content=cf)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertNotIn("[MATCHING CONFIGURATION] OK", output)
        self.assertIn("ERROR: [MATCHING CONFIGURATION]", output)

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
        self.assertIn("ERROR: [MATCHING CONFIGURATION]", output)  # Empty package
        self.assertIn("[SHARED ARTIFACTS] OK", output)
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
        self.assertIn("[SHARED ARTIFACTS] OK", output)
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
        self.assertIn("[SHARED ARTIFACTS] OK", output)
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
        self.assertIn("ERROR: [MATCHING CONFIGURATION] Built artifacts does not match the settings",
                      output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)

    def test_regular_folder_size(self):
        tools.save('conanfile.py', content=self.conanfile_installer)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[RECIPE FOLDER SIZE] OK", output)
        self.assertNotIn("ERROR: [RECIPE FOLDER SIZE]", output)

    def test_larger_folder_size(self):
        content = " ".join(["test_recipe_folder_larger_size" for it in range(1048576)])
        tools.save('conanfile.py', content=self.conanfile_installer)
        tools.save('big_file', content=content)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [RECIPE FOLDER SIZE] The size of your recipe folder", output)

    def test_custom_folder_size(self):
        with tools.environment_append({"CONAN_MAX_RECIPE_FOLDER_SIZE_KB": "0"}):
            tools.save('conanfile.py', content=self.conanfile_installer)
            output = self.conan(['export', '.', 'name/version@user/channel'])
            self.assertIn("ERROR: [RECIPE FOLDER SIZE] The size of your recipe folder", output)
