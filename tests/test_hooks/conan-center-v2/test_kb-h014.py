import os
import shutil
import textwrap
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH014(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                        from conan import ConanFile
                        class AConan(ConanFile):
                            exports_sources = "{placeholder}"                       
                        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH014, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_export_files(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="*"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[EXPORT LICENSE (KB-H014)] OK" in output

    def test_export_license(self):
        save(self, 'LICENSE', content="LICENSE")
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="LICENSE"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [EXPORT LICENSE (KB-H014)] The ConanCenterIndex does not allow exporting recipes" in output