import os
import shutil
import textwrap
from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class TestKBH004(ConanClientV2TestCase):

    conanfile_base = textwrap.dedent("""\
            from conan import ConanFile
            class AConan(ConanFile):
                name = "package"   
                {placeholder}             
            """)
    conanfile_header_only = textwrap.dedent("""\
            from conan import ConanFile
            class AConan(ConanFile):
                name = "package"                
                settings = "os", "compiler", "arch", "build_type"
                
                def package_id(self):
                    self.info.clear()
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH004, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_settings(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder=''))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "[FPIC OPTION (KB-H004)] OK" in output

    def test_with_settings(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='settings = "os"'))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "WARN: [FPIC OPTION (KB-H004)] This recipe does not include an 'fPIC' option. Make sure you are using the right casing" in output

    def test_header_only(self):
        save(self, 'conanfile.py', content=self.conanfile_header_only)
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "[FPIC OPTION (KB-H004)] OK" in output
        assert "WARN: [FPIC OPTION (KB-H004)]" not in output