import os
import shutil
import textwrap
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save, mkdir


class TestKBH015(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                        from conan import ConanFile
                        class AConan(ConanFile):
                            pass                       
                        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH015, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_test_package(self):
        save(self, 'conanfile.py', content=self.conanfile)
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [TEST PACKAGE FOLDER (KB-H015)] There is no 'test_package' for this recipe" in output

    def test_with_test_package_folder(self):
        save(self, 'conanfile.py', content=self.conanfile)
        mkdir(self, 'test_package')
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [TEST PACKAGE FOLDER (KB-H015)] There is no 'conanfile.py' in 'test_package' folder" in output

    def test_with_test_package_file(self):
        save(self, 'conanfile.py', content=self.conanfile)
        save(self, 'test_package/conanfile.py', content=self.conanfile)
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[TEST PACKAGE FOLDER (KB-H015)] OK" in output