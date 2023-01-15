import os
import textwrap

from parameterized import parameterized

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestPackagingStaticSharedLibraries(ConanClientTestCase):
    conanfile_test_artifacts = textwrap.dedent("""\
        from conan import ConanFile
        import os

        class AConan(ConanFile):
            settings = "os", "arch", "compiler", "build_type"
            options = {"shared": [True, False], "status": [True, False]}
            default_options = {"shared": False, "status": True}

            def package(self):
                libdir = os.path.join(self.package_folder, "lib")
                os.makedirs(libdir)
                if self.options.status:
                    if self.options.shared:
                        open(os.path.join(libdir, "libfoo.so"), "w")
                    else:
                        open(os.path.join(libdir, "libfoo.a"), "w")
                else:
                    if self.options.shared:
                        open(os.path.join(libdir, "libfoo.a"), "w")
                    else:
                        open(os.path.join(libdir, "libfoo.so"), "w")

            def package_info(self):
                self.cpp_info.libs = ["foo"]
        """)

    conanfile_test_static_or_shared = textwrap.dedent("""\
        from conan import ConanFile
        import os

        class AConan(ConanFile):
            settings = "os", "arch", "compiler", "build_type"
            options = {"shared": [True, False], "status": [True, False]}
            default_options = {"shared": False, "status": True}

            def package(self):
                libdir = os.path.join(self.package_folder, "lib")
                os.makedirs(libdir)
                if self.options.status:
                    if self.options.shared:
                        open(os.path.join(libdir, "libfoo.so"), "w")
                        open(os.path.join(libdir, "libbar.so"), "w")
                    else:
                        open(os.path.join(libdir, "libfoo.a"), "w")
                        open(os.path.join(libdir, "libbar.a"), "w")
                else:
                    open(os.path.join(libdir, "libfoo.a"), "w")
                    open(os.path.join(libdir, "libfoo.so"), "w")
                    open(os.path.join(libdir, "libbar.a"), "w")

            def package_info(self):
                self.cpp_info.libs = ["foo"]
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestPackagingStaticSharedLibraries, self)._get_environ(**kwargs)
        kwargs.update({
            "CONAN_HOOKS": os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                                        os.pardir, "hooks", "conan-center")
        })
        return kwargs

    @parameterized.expand([(True, True), (True, False), (False, True), (False, False)])
    def test_artifacts(self, shared, hook_ok):
        tools.save("conanfile.py", content=self.conanfile_test_artifacts)
        output = self.conan([
            "create", ".", "name/version@user/test",
            "-o", f"name:shared={shared}",
            "-o", f"name:status={hook_ok}",
        ])
        if hook_ok:
            self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
            self.assertIn("[STATIC ARTIFACTS (KB-H074)] OK", output)
        elif shared:
            self.assertIn("ERROR: [SHARED ARTIFACTS (KB-H015)] Package with 'shared=True' option did not contain any shared artifact", output)
            self.assertIn("[STATIC ARTIFACTS (KB-H074)] OK", output)
        else:
            self.assertIn("[SHARED ARTIFACTS (KB-H015)] OK", output)
            self.assertIn("ERROR: [STATIC ARTIFACTS (KB-H074)] Package with 'shared=False' option did not contain any static artifact", output)

    @parameterized.expand([(True, True), (True, False), (False, True), (False, False)])
    def test_either_shared_or_static(self, shared, hook_ok):
        tools.save("conanfile.py", content=self.conanfile_test_static_or_shared)
        output = self.conan([
            "create", ".", "name/version@user/test",
            "-o", f"name:shared={shared}",
            "-o", f"name:status={hook_ok}",
        ])
        if hook_ok:
            self.assertIn("[EITHER STATIC OR SHARED OF EACH LIB (KB-H076)] OK", output)
        else:
            self.assertIn("ERROR: [EITHER STATIC OR SHARED OF EACH LIB (KB-H076)] Package contains both shared and static flavors of these libraries: libfoo", output)
