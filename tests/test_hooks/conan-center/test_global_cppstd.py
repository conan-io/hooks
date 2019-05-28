import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestGlobalCPPSTD(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            settings = "cppstd"
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestGlobalCPPSTD, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_forbidden_usage(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [GLOBAL CPPSTD DEPRECATED] The 'cppstd' setting is deprecated. "
                      "Use the 'compiler.cppstd' subsetting instead", output)

    def test_forbidden_usage_multi_settings(self):
        tools.save('conanfile.py', content=self.conanfile.replace('"cppstd"', '"cppstd", "os"'))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [GLOBAL CPPSTD DEPRECATED] The 'cppstd' setting is deprecated. "
                      "Use the 'compiler.cppstd' subsetting instead", output)

    def test_ok_usage(self):
        tools.save('conanfile.py', content=self.conanfile.replace("cppstd", "os"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [GLOBAL CPPSTD DEPRECATED] ", output)

