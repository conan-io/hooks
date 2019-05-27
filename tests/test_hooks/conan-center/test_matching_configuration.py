import os
import textwrap
import platform

from conans import tools
from parameterized import parameterized

from tests.utils.test_cases.conan_client import ConanClientTestCase


class MatchingConfigurationTests(ConanClientTestCase):
    conanfile_match_conf = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            exports_sources = "file.{extension}", "LICENSE"
            {settings}

            def package(self):
                self.copy("*")
    """)

    def _get_environ(self, **kwargs):
        kwargs = super(MatchingConfigurationTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    @parameterized.expand([("Windows", "lib"), ("Darwin", "so"), ("Linux", "so")])
    def test_matching_configuration(self, system_name, extension):
        cf = self.conanfile_match_conf.format(extension=extension,
                                              settings="settings = 'os', 'compiler', 'arch', "
                                                       "'build_type'")
        tools.save('conanfile.py', content=cf)
        tools.save('file.%s' % extension, content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        if platform.system() == system_name:
            self.assertIn("[MATCHING CONFIGURATION] OK", output)
            self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)
        else:
            self.assertNotIn("[MATCHING CONFIGURATION] OK", output)
            self.assertIn("ERROR: [MATCHING CONFIGURATION]", output)

    @parameterized.expand([("Windows", "so", "Package for Visual Studio does not contain artifacts "
                                             "with these extensions: ['lib', 'dll', 'exe']"),
                           ("Darwin", "lib", "Package for Macos does not contain artifacts "
                                             "with these extensions: ['a', 'dylib', '']"),
                           ("Linux", "exe", "Package for Linux does not contain artifacts "
                                            "with these extensions: ['a', 'so', '']")])
    def test_mismatching_configuration(self, system_name, extension, error_message):
        cf = self.conanfile_match_conf.format(extension=extension,
                                              settings="settings = 'os', 'compiler', 'arch', "
                                                       "'build_type'")
        tools.save('conanfile.py', content=cf)
        tools.save('file.%s' % extension, content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        if platform.system() == system_name:
            self.assertNotIn("[MATCHING CONFIGURATION] OK", output)
            self.assertIn("ERROR: [MATCHING CONFIGURATION] %s" % error_message, output)
        else:
            self.assertIn("[MATCHING CONFIGURATION] OK", output)
            self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)

    def test_matching_configuration_header_only_package_id(self):
        cf = self.conanfile_match_conf.format(extension="h",
                                              settings="settings = 'os', 'compiler', 'arch', "
                                                       "'build_type'")
        cf = cf + """
    def package_id(self):
        self.info.header_only()
        """
        tools.save('conanfile_other.py', content=cf)
        tools.save('file.h', content="")
        tools.save('LICENSE', content="")
        output = self.conan(['create', 'conanfile_other.py', 'name/version@danimtb/test'])
        self.assertIn("[MATCHING CONFIGURATION] OK", output)
        self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)

    def test_matching_configuration_header_only(self):
        cf = self.conanfile_match_conf.format(extension="h",
                                              settings="")
        tools.save('conanfile.py', content=cf)
        tools.save('file.h', content="")
        tools.save('LICENSE', content="")
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
        self.assertIn("ERROR: [MATCHING CONFIGURATION] Empty package", output)

    @parameterized.expand([("Windows", "exe"), ("Darwin", ""), ("Linux", "")])
    def test_matching_configuration_tool(self, system_name, extension):
        cf = self.conanfile_match_conf.format(extension="exe",
                                              settings="settings = 'os'")
        tools.save('conanfile.py', content=cf)
        tools.save('file.%s' % extension, content="")
        output = self.conan(['create', '.', 'name/version@jgsogo/test'])
        if platform.system() == system_name:
            self.assertIn("[MATCHING CONFIGURATION] OK", output)
            self.assertNotIn("ERROR: [MATCHING CONFIGURATION]", output)
        else:
            self.assertNotIn("[MATCHING CONFIGURATION] OK", output)
            self.assertIn("ERROR: [MATCHING CONFIGURATION]", output)
