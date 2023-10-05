import os
import shutil
import textwrap
from parameterized import parameterized

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save

class TestKBH011(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import save, mkdir
            import os

            class AConan(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                options = {"shared": [True, False], "status": [True, False]}
                default_options = {"shared": False, "status": True}

                def package(self):
                    libdir = os.path.join(self.package_folder, "lib")
                    mkdir(self, libdir)
                    if self.options.status:
                        if self.options.shared:
                            save(self, os.path.join(libdir, "libfoo.so"), "whatever")
                        else:
                            save(self, os.path.join(libdir, "libfoo.a"), "whatever")
                    else:
                        if self.options.shared:
                            save(self, os.path.join(libdir, "libfoo.a"), "whatever")
                        else:
                            save(self, os.path.join(libdir, "libfoo.so"), "whatever")

                def package_info(self):
                    self.cpp_info.libs = ["foo"]
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH011, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    @parameterized.expand([(True, True), (True, False), (False, True), (False, False)])
    def test_artifacts(self, shared, hook_ok):
        save(self, "conanfile.py", content=self.conanfile)
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", f"foobar/0.1.0:shared={shared}", "-o", f"foobar/0.1.0:status={hook_ok}"])
        print(f"shared={shared}, hook_ok={hook_ok}")
        if hook_ok:
            assert "[MATCHING CONFIGURATION (KB-H011)] OK" in output
        elif shared:
            assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package with 'shared=True' option did not contain any shared artifact" in output
            assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package type is 'shared-library' but contains static libraries" in output
        else:
            assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package with 'shared=False' option did not contain any static artifact" in output
            assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package type is 'static-library' but contains shared libraries" in output