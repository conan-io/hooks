import os
import shutil
import textwrap
from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class TestKBH006(ConanClientV2TestCase):

    conanfile_base = textwrap.dedent("""\
            from conan import ConanFile
            class AConan(ConanFile):
                name = "package"   
                {placeholder}             
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH006, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_regular_folder(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder=''))
        output = self.conan(['export', '--name=package', '--version=0.1.0', 'conanfile.py'])
        assert "[RECIPE FOLDER SIZE (KB-H006)] OK" in output

    def test_max_size_folder(self):
        # create a file of 300KB
        with open("bigfile", "wb") as file:
            while file.tell() < 300 * 1024:
                file.write(b'\x00' * 1024)
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='exports = "bigfile"'))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "ERROR: [RECIPE FOLDER SIZE (KB-H006)] The size of your recipe folder" in output