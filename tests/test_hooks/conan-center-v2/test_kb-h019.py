import os
import shutil
import textwrap
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save
from parameterized import parameterized


class TestKBH019(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""
                        from conan import ConanFile                        
                        class AConan(ConanFile):
                            {placeholder} = None
                        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH019, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_regular_package(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="foobar"))
        output = self.conan(['export', '--name=foobar', '--version=system', 'conanfile.py'])
        assert "[NOT ALLOWED ATTRIBUTES (KB-H019)] OK" in output

    @parameterized.expand([("build_policy", ), ("upload_policy", ), ("package_id_embed_mode"), ("package_id_non_embed_mode"), ("package_id_unknown_mode")])
    def test_regular_package(self, attribute):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder=attribute))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [NOT ALLOWED ATTRIBUTES (KB-H019)] Some attributes are affecting the packaging behavior and are not allowed" in output