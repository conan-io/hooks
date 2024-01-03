import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH029(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conan import ConanFile
        class AConan(ConanFile):
            {placeholder}
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH029, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_default_options(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="pass"))
        save(self, 'test_package/conanfile.py', content=self.conanfile.format(placeholder="pass"))
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "[TEST PACKAGE - NO DEFAULT OPTIONS (KB-H029)]" in output

    def test_with_default_options(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="pass"))
        save(self, 'test_package/conanfile.py', content=self.conanfile.format(placeholder="default_options = {'name:foo': True}"))
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [TEST PACKAGE - NO DEFAULT OPTIONS (KB-H029)] The attribute 'default_options' is not allowed on test_package/conanfile.py, remove it." in output