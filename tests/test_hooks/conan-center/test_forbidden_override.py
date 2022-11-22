import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ForbiddenOverrideTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conan import ConanFile

        class AConan(ConanFile):           
           def requirements(self):
               {}
               pass
 
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(ForbiddenOverrideTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_with_override_true(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "self.requires('package/version', override=True)"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [REQUIREMENT OVERRIDE PARAMETER (KB-H075)]", output)

    def test_with_override_false(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "self.requires('package/version', override=False)"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[REQUIREMENT OVERRIDE PARAMETER (KB-H075)] OK", output)

    def test_no_requires(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", ""))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[REQUIREMENT OVERRIDE PARAMETER (KB-H075)] OK", output)

    def test_with_private_false(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "self.requires('package/version', private=False, override=False)"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[REQUIREMENT OVERRIDE PARAMETER (KB-H075)] OK", output)

    def test_with_private_true(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "self.requires('package/version', override=True, private=False)"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [REQUIREMENT OVERRIDE PARAMETER (KB-H075)]", output)
