import os
import platform
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save
from conan.cli.exit_codes import SUCCESS, ERROR_INVALID_CONFIGURATION

class TestKBH005(ConanClientV2TestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH005, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_fpic_remove(self):
        conanfile = textwrap.dedent("""\
                from conan import ConanFile

                class LinuxOnly(ConanFile):
                    url = "fake_url.com"
                    license = "fake_license"
                    description = "whatever"
                    settings = "os", "arch", "compiler", "build_type"
                    options = {"fPIC": [True, False], "shared": [True, False]}
                    default_options = {"fPIC": True, "shared": False}
                """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['export', '--name=package', '--version=0.1.0', 'conanfile.py'])
        assert "[FPIC OPTION (KB-H004)] OK" in output

        output = self.conan(['build', '--name=package', '--version=0.1.0', 'conanfile.py'])
        if platform.system() == "Windows":
            assert "ERROR: [FPIC MANAGEMENT (KB-H005)] 'fPIC' option not managed " \
                   "correctly. Please remove it for Windows " \
                   "configurations: del self.options.fPIC" in output
        else:
            assert "[FPIC MANAGEMENT (KB-H005)] OK. 'fPIC' option found and apparently well managed" in output

        output = self.conan(['build', '--name=package', '--version=0.1.0', 'conanfile.py', '-o package/0.1.0:shared=True'])
        assert "ERROR: [FPIC MANAGEMENT (KB-H005)] 'fPIC' option not managed correctly. Please remove it for shared option: del self.options.fPIC" in output

    def test_fpic_remove_windows(self):
        conanfile = textwrap.dedent("""\
                from conan import ConanFile

                class Conan(ConanFile):
                    url = "fake_url.com"
                    license = "fake_license"
                    description = "whatever"
                    settings = "os", "arch", "compiler", "build_type"
                    options = {"fPIC": [True, False], "shared": [True, False]}
                    default_options = {"fPIC": True, "shared": False}

                    def config_options(self):
                        if self.settings.os == "Windows":
                            del self.options.fPIC
                """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['export', '.', '--name=package', '--version=0.1.0'])
        assert "[FPIC OPTION (KB-H004)] OK" in output

        output = self.conan(['build', '--name=package', '--version=0.1.0', 'conanfile.py'])
        if platform.system() == "Windows":
            assert "[FPIC MANAGEMENT (KB-H005)] 'fPIC' option not found" in output
        else:
            assert "[FPIC MANAGEMENT (KB-H005)] OK. 'fPIC' option found and apparently well managed" in output
        assert "[FPIC MANAGEMENT (KB-H005)] OK" in output

    def test_fpic_remove_windows_configuration(self):
        conanfile = textwrap.dedent("""\
                from conan import ConanFile
                from conan.errors import ConanInvalidConfiguration

                class Conan(ConanFile):
                    url = "fake_url.com"
                    license = "fake_license"
                    description = "whatever"
                    settings = "os", "arch", "compiler", "build_type"
                    options = {"fPIC": [True, False], "shared": [True, False]}
                    default_options = {"fPIC": True, "shared": False}

                    def configure(self):
                        if self.settings.os == "Windows":
                            raise ConanInvalidConfiguration("Windows not supported")
                """)
        save(self, 'conanfile.py', content=conanfile)
        self.conan(['export', '.', '--name=package', '--version=0.1.0'])
        expected_return_code = ERROR_INVALID_CONFIGURATION if platform.system() == "Windows" else SUCCESS
        output = self.conan(['build', '--name=package', '--version=0.1.0', 'conanfile.py'], expected_return_code)
        if platform.system() == "Windows":
            assert "[FPIC MANAGEMENT (KB-H005)] OK" not in output
        else:
            assert "[FPIC MANAGEMENT (KB-H005)] OK. 'fPIC' option found and apparently well managed" in output