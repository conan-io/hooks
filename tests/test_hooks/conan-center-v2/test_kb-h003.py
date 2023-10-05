import os
import shutil
import textwrap
from parameterized import parameterized
from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class TestKBH003(ConanClientV2TestCase):

    conanfile_base = textwrap.dedent("""\
            from conan import ConanFile
            class AConan(ConanFile):
                name = "package"   
                {placeholder}             
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH003, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_copy_source(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder=''))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "WARN: [HEADER_ONLY, NO COPY SOURCE (KB-H003)] This recipe is a header only library as it does not declare 'settings'. Please include 'no_copy_source' to avoid unnecessary copy steps" in output

    def test_no_copy_source_with_settings(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='settings = "os"'))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "WARN: [HEADER_ONLY, NO COPY SOURCE (KB-H003)]" not in output

    def test_with_copy_source(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='no_copy_source = True'))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "WARN: [HEADER_ONLY, NO COPY SOURCE (KB-H003)]" not in output