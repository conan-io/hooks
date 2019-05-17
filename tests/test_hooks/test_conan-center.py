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
            {placeholder}
        """)
    conanfile_header_only = conanfile_base.format(placeholder='pass')
    conanfile_installer = conanfile_base.format(placeholder='settings = "os_build"')
    conanfile = conanfile_base.format(placeholder='settings = "os"')

    def _get_environ(self, **kwargs):
        kwargs = super(ConanCenterTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks',
                                                   'conan-center')})
        return kwargs

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
        self.assertIn("[MATCHING CONFIGURATION] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)
        self.assertIn("ERROR: [PACKAGE LICENSE] No 'licenses' folder found in package", output)
        self.assertIn("[DEFAULT PACKAGE LAYOUT] OK", output)
        self.assertIn("[SHARED ARTIFACTS] OK", output)
        print(output)

    def test_conanfile_header_only(self):
        tools.save('conanfile.py', content=self.conanfile_header_only)
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        self.assertIn("[RECIPE METADATA] OK", output)
        self.assertIn("[HEADER ONLY] OK", output)
        self.assertIn("[NO COPY SOURCE] This recipe seems to be for a header only", output)
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
            content = " ".join(["test_recipe_folder_larger_size" for it in range(1048576)])
            tools.save('conanfile.py', content=self.conanfile_installer)
            output = self.conan(['export', '.', 'name/version@user/channel'])
            self.assertIn("ERROR: [RECIPE FOLDER SIZE] The size of your recipe folder", output)
