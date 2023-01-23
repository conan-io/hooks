import os
import platform
import textwrap

from parameterized import parameterized

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestPackageInfoWindowsLowercaseSystemLibs(ConanClientTestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestPackageInfoWindowsLowercaseSystemLibs, self)._get_environ(**kwargs)
        kwargs.update({
            "CONAN_HOOKS": os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                                        os.pardir, "hooks", "conan-center")
        })
        return kwargs

    @staticmethod
    def _conanfile_test_global_cpp_info(system_lib=None):
        system_libs = "[{}]".format(f"\"{system_lib}\"" if system_lib else "")
        return textwrap.dedent(f"""\
            from conan import ConanFile
            import os

            class AConan(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                options = {{"shared": [True, False], "status": [True, False]}}
                default_options = {{"shared": False, "status": True}}

                def package_info(self):
                    if self.settings.os == "Windows":
                        self.cpp_info.system_libs = {system_libs}
                    else:
                        self.cpp_info.system_libs = ["FOO"]
        """)

    @staticmethod
    def _conanfile_test_components_cpp_info(system_lib_a=None, system_lib_b=None):
        system_libs_a = "[{}]".format(f"\"{system_lib_a}\"" if system_lib_a else "")
        system_libs_b = "[{}]".format(f"\"{system_lib_b}\"" if system_lib_b else "")
        return textwrap.dedent(f"""\
            from conan import ConanFile
            import os

            class AConan(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                options = {{"shared": [True, False], "status": [True, False]}}
                default_options = {{"shared": False, "status": True}}

                def package_info(self):
                    if self.settings.os == "Windows":
                        self.cpp_info.components["a"].system_libs = {system_libs_a}
                        self.cpp_info.components["b"].system_libs = {system_libs_b}
                    else:
                        self.cpp_info.components["a"].system_libs = ["FOO"]
                        self.cpp_info.components["b"].system_libs = ["BAR"]
        """)

    @parameterized.expand([(None, ), ("ws2_32", ), ("Ws2_32", )])
    def test_global_cpp_info(self, system_lib):
        tools.save("conanfile.py", content=self._conanfile_test_global_cpp_info(system_lib))
        output = self.conan(["create", ".", "name/version@user/test"])
        if platform.system() != "Windows" or not system_lib or system_lib.islower():
            self.assertIn("[WINDOWS LOWERCASE SYSTEM LIBS (KB-H078)] OK", output)
        else:
            error_message = (
                "ERROR: [WINDOWS LOWERCASE SYSTEM LIBS (KB-H078)] "
                "All libs listed in system_libs should be lowercase if host OS is "
                "Windows to support both native Windows build and cross-build from Linux. "
                f"Found system libs with uppercase characters: {system_lib}"
            )
            self.assertIn(error_message, output)

    @parameterized.expand([
        (None, None),
        ("ws2_32", "ole32"),
        ("Ws2_32", "ole32"),
        ("ws2_32", "Ole32"),
        ("Ws2_32", "Ole32"),
    ])
    def test_components_cpp_info(self, system_lib_a, system_lib_b):
        tools.save("conanfile.py", content=self._conanfile_test_components_cpp_info(system_lib_a, system_lib_b))
        output = self.conan(["create", ".", "name/version@user/test"])
        if platform.system() != "Windows" or \
           ((not system_lib_a or system_lib_a.islower()) and \
            (not system_lib_b or system_lib_b.islower())):
            self.assertIn("[WINDOWS LOWERCASE SYSTEM LIBS (KB-H078)] OK", output)
        else:
            uppercase_libs = []
            if system_lib_a and not system_lib_a.islower():
                uppercase_libs.append(system_lib_a)
            if system_lib_b and not system_lib_b.islower():
                uppercase_libs.append(system_lib_b)
            uppercase_libs.sort()
            error_message = (
                "ERROR: [WINDOWS LOWERCASE SYSTEM LIBS (KB-H078)] "
                "All libs listed in system_libs should be lowercase if host OS is "
                "Windows to support both native Windows build and cross-build from Linux. "
                f"Found system libs with uppercase characters: {', '.join(uppercase_libs)}"
            )
            self.assertIn(error_message, output)
