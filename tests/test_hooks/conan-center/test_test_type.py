import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestTestType(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
                pass
        """)
    test_conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class TestConan(ConanFile):
            test_type = "{}"

            def test(self):
                pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestTestType, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_type_explicit(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('test_package/conanfile.py', content=self.test_conanfile.replace("{}", "explicit"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[TEST_TYPE MANAGEMENT (KB-H068)] OK", output)

    def test_type_requires(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('test_package/conanfile.py', content=self.test_conanfile.replace("{}", "requires"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [TEST_TYPE MANAGEMENT (KB-H068)] The attribute 'test_type' only should be used with 'explicit' value.", output)

    def test_type_build_requires(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('test_package/conanfile.py', content=self.test_conanfile.replace("{}", "build_requires"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [TEST_TYPE MANAGEMENT (KB-H068)] The attribute 'test_type' only should be used with 'explicit' value.", output)

    def test_no_test_type(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('test_package/conanfile.py', content=self.conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[TEST_TYPE MANAGEMENT (KB-H068)] OK", output)
