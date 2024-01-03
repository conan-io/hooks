import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH022(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile            
            class AConan(ConanFile):
                options = {"shared": [True, False]}
                default_options = {"shared": {placeholder}}
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH022, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_default_shared_true(self):
        save(self, os.path.join('all', 'conanfile.py'), content=self.conanfile.replace('{placeholder}', 'True'))
        output = self.conan(['export', 'all', '--name=name', '--version=0.1.0'])
        assert "ERROR: [DEFAULT SHARED OPTION VALUE (KB-H022)] The option 'shared' must be 'False' by default" in output

    def test_default_shared_false(self):
        save(self, os.path.join('all', 'conanfile.py'), content=self.conanfile.replace('{placeholder}', 'False'))
        output = self.conan(['export', 'all', '--name=name', '--version=0.1.0'])
        assert "[DEFAULT SHARED OPTION VALUE (KB-H022)] OK" in output