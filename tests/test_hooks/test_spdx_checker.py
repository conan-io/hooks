import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class SPDXCheckerTest(ConanClientTestCase):
    def _get_environ(self, **kwargs):
        kwargs = super(SPDXCheckerTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(
            __file__), '..', '..', 'hooks', 'spdx_checker')})
        return kwargs

    def test_valid_license_name(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            license = "BSL-1.0"
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])

        self.assertNotIn("recipe doesn't have a license attribute", output)
        self.assertIn('license "BSL-1.0" is a valid SPDX license identifier', output)

    def test_valid_license_list_names(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            license = "Zlib", "MIT", "BSD-3-Clause"
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])

        self.assertNotIn("recipe doesn't have a license attribute", output)
        self.assertIn('license "Zlib" is a valid SPDX license identifier', output)
        self.assertIn('license "MIT" is a valid SPDX license identifier', output)
        self.assertIn('license "BSD-3-Clause" is a valid SPDX license identifier', output)

    def test_no_license_attribute(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            pass
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("recipe doesn't have a license attribute", output)

    def test_invalid_license_name(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            license = "Apache-2.0", "Invalid-License"
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])

        self.assertNotIn("recipe doesn't have a license attribute", output)
        self.assertIn('license "Apache-2.0" is a valid SPDX license identifier', output)
        self.assertIn('license "Invalid-License" is not a valid SPDX license identifier', output)

    def test_case_sensitive(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            license = "zlib"
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])

        self.assertNotIn("recipe doesn't have a license attribute", output)
        self.assertIn('license "zlib" is not a valid SPDX license identifier', output)

    def test_wrong_attribute_type(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            license = {"name": "Zlib"}
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])

        self.assertNotIn("recipe doesn't have a license attribute", output)
        self.assertIn("don't know how to process license attribute which is neither string nor tuple", output)
