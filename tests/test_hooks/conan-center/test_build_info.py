import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestBuildInfo(ConanClientTestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestBuildInfo, self)._get_environ(**kwargs)
        kwargs.update({"CONAN_HOOKS": os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                                   "hooks", "conan-center")})
        return kwargs

    def test_trivial_ok(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
            from conans import ConanFile

            class AConan(ConanFile):
                pass
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("[NO BUILD SYSTEM FUNCTIONS (KB-H061)] OK", output)

    def test_build_toolsosinfo_ok(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
            from conans import ConanFile, tools

            class AConan(ConanFile):
                def build(self):
                    if tools.os_info.is_windows:
                        print("We're on Windows")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("[NO BUILD SYSTEM FUNCTIONS (KB-H061)] OK", output)

    def test_build_platform_ok(self):
        tools.save("conanfile.py", content=textwrap.dedent("""\
            from conans import ConanFile
            import platform

            class AConan(ConanFile):
                def build(self):
                    if platform.system() == "Linux":
                        print("We're on Linux")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("[NO BUILD SYSTEM FUNCTIONS (KB-H061)] OK", output)

    def test_buildreq_toolsosinfo(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools

            class AConan(ConanFile):
                def build_requirements(self):
                    if tools.os_info.is_windows and not tools.get_env("CONAN_BASH_PATH"):
                        self.build_requires("msys2/cci.latest")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of tools.os_info is forbidden in build_requirements", output)
        self.assertIn("conanfile.py:5 Build system dependent", output)

    def test_buildreq_platform(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools
            import platform

            class AConan(ConanFile):
                def build_requirements(self):
                    if platform.system() == "Windows" and not tools.get_env("CONAN_BASH_PATH"):
                        self.build_requires("msys2/cci.latest")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of platform is forbidden in build_requirements", output)
        self.assertIn("conanfile.py:6 Build system dependent", output)

    def test_req_toolsosinfo(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools

            class AConan(ConanFile):
                def requirements(self):
                    if tools.os_info.is_linux:
                        self.requires("libalsa/1.2.4")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of tools.os_info is forbidden in requirements", output)
        self.assertIn("conanfile.py:5 Build system dependent", output)

    def test_req_platform(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools
            import platform

            class AConan(ConanFile):
                def requirements(self):
                    if platform.system() == "Linux":
                        self.requires("libalsa/1.2.4")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of platform is forbidden in requirements", output)
        self.assertIn("conanfile.py:6 Build system dependent", output)

    def test_configopts_toolsosinfo(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools

            class AConan(ConanFile):
                options = {
                    "fPIC": [True, False],
                }

                def config_options(self):
                    if tools.os_info.is_windows:
                        del self.options.fPIC
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of tools.os_info is forbidden in config_options", output)
        self.assertIn("conanfile.py:9 Build system dependent", output)

    def test_configopts_platform(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools
            import platform

            class AConan(ConanFile):
                options = {
                    "fPIC": [True, False],
                }

                def config_options(self):
                    if platform.system == "Windows":
                        del self.options.fPIC
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of platform is forbidden in config_options", output)
        self.assertIn("conanfile.py:10 Build system dependent", output)

    def test_config_toolsosinfo(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools

            class AConan(ConanFile):
                options = {
                    "fPIC": [True, False],
                }

                def configure(self):
                    if tools.os_info.is_windows:
                        del self.options.fPIC
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of tools.os_info is forbidden in configure", output)
        self.assertIn("conanfile.py:9 Build system dependent", output)

    def test_config_platform(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools
            import platform

            class AConan(ConanFile):
                options = {
                    "fPIC": [True, False],
                }

                def configure(self):
                    if platform.system == "Windows":
                        del self.options.fPIC
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of platform is forbidden in configure", output)
        self.assertIn("conanfile.py:10 Build system dependent", output)

    def test_validate_toolsosinfo(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools
            from conans.errors import ConanInvalidConfiguration

            class AConan(ConanFile):
                options = {
                    "fPIC": [True, False],
                }

                def validate(self):
                    if tools.os_info.is_windows:
                        raise ConanInvalidConfiguration("I refuse to build on Windows")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of tools.os_info is forbidden in validate", output)
        self.assertIn("conanfile.py:10 Build system dependent", output)

    def test_validate_platform(self):
        tools.save("conanfile.py", textwrap.dedent("""\
            from conans import ConanFile, tools
            from conans.errors import ConanInvalidConfiguration
            import platform

            class AConan(ConanFile):
                options = {
                    "fPIC": [True, False],
                }

                def validate(self):
                    if platform.system == "Windows":
                        raise ConanInvalidConfiguration("I refuse to build on Windows")
            """))
        output = self.conan(["export", ".", "name/version@user/channel"])
        self.assertIn("ERROR: [NO BUILD SYSTEM FUNCTIONS (KB-H061)]", output)
        self.assertIn("Use of platform is forbidden in validate", output)
        self.assertIn("conanfile.py:11 Build system dependent", output)
