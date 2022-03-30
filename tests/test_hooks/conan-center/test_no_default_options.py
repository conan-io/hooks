import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class NoDefaultOptionsTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):
            {}
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(NoDefaultOptionsTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_no_default_options(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "pass"))
        tools.save('test_package/conanfile.py', content=self.conanfile.replace("{}", "pass"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[TEST PACKAGE - NO DEFAULT OPTIONS (KB-H069)]", output)

    def test_with_default_options(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "pass"))
        tools.save('test_package/conanfile.py',
                   content=self.conanfile.replace("{}", "default_options = {'name:foo': True}"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [TEST PACKAGE - NO DEFAULT OPTIONS (KB-H069)] The attribute"
                      " 'default_options' is not allowed on test_package/conanfile.py, remove it.",
                      output)
