import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestSkipPylint(ConanClientTestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestSkipPylint, self)._get_environ(**kwargs)
        kwargs.update({"CONAN_HOOKS": os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                                   "hooks", "conan-center")})
        return kwargs

    def test_trivial_ok(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
            from conan import ConanFile

            class AConan(ConanFile):
                pass
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("[PYLINT EXECUTION (KB-H072)] OK", output)

    def test_pylint_comment(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
            from conan import ConanFile

            class AConan(ConanFile):
                def configure(self):
                    pass #pylint: this is a comment
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("[PYLINT EXECUTION (KB-H072)] OK", output)

    def test_pylint_skip_file(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
            # pylint: skip-file
            from conan import ConanFile
            
            class AConan(ConanFile):
                pass
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [PYLINT EXECUTION (KB-H072)] Pylint can not be skipped", output)

    def test_pylint_disable_all(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
                    #pylint: disable-all
                    from conan import ConanFile

                    class AConan(ConanFile):
                        pass
                    """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [PYLINT EXECUTION (KB-H072)] Pylint can not be skipped", output)

    def test_pylint_disable_locally(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
                    # pylint : disable=locally-disabled, multiple-statements, fixme, line-too-long
                    from conan import ConanFile

                    class AConan(ConanFile):
                        pass
                    """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [PYLINT EXECUTION (KB-H072)] Pylint can not be skipped", output)

    def test_pylint_test_package_alone(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
                    from conan import ConanFile
                    class AConan(ConanFile):
                        pass
                    """))
        tools.save("test_package/conanfile.py", content=textwrap.dedent("""\
                    #pylint: skip-file
                    from conan import ConanFile
                    class AConan(ConanFile):
                        pass
                    """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [PYLINT EXECUTION (KB-H072)] Pylint can not be skipped", output)

    def test_pylint_test_v1_package(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
                    from conan import ConanFile
                    class AConan(ConanFile):
                        pass
                    """))
        tools.save("test_package/conanfile.py", content=textwrap.dedent("""\
                    from conan import ConanFile
                    class AConan(ConanFile):
                        pass
                    """))
        tools.save("test_v1_package/conanfile.py", content=textwrap.dedent("""\
                    #pylint: skip-file
                    from conan import ConanFile
                    class AConan(ConanFile):
                        pass
                    """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [PYLINT EXECUTION (KB-H072)] Pylint can not be skipped", output)
