import os
import shutil
import textwrap
from parameterized import parameterized
from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class TestKBH002(ConanClientV2TestCase):
    conanfile_empty = textwrap.dedent("""\
        from conan import ConanFile
        class AConan(ConanFile):
           {placeholder}
           pass

        """)
    conanfile_base = textwrap.dedent("""\
            from conan import ConanFile
            class AConan(ConanFile):
                name = "name"                
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH002, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_say_my_name(self):
        save(self, 'conanfile.py', content=self.conanfile_empty.format(placeholder=''))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "ERROR: [RECIPE REFERENCE (KB-H002)] The 'name' attribute should be declared with the package name" in output

    def test_version_attributes(self):
        save(self, 'conanfile.py', content=self.conanfile_empty.format(placeholder=f"version = '0.1.0'"))
        output = self.conan(['export', '--name=package', 'conanfile.py'])
        assert f"ERROR: [RECIPE REFERENCE (KB-H002)] The attribute 'version' should not be declared in the recipe. Please, remove it." in output

    def test_user_attributes(self):
        save(self, 'conanfile.py', content=self.conanfile_empty.format(placeholder=f"user = 'bar'"))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--channel=testing', 'conanfile.py'])
        assert f"ERROR: [RECIPE REFERENCE (KB-H002)] The attribute 'user' should not be declared in the recipe. Please, remove it." in output

    def test_channel_attributes(self):
        save(self, 'conanfile.py', content=self.conanfile_empty.format(placeholder=f"channel = 'testing'"))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=foobar', 'conanfile.py'])
        assert f"ERROR: [RECIPE REFERENCE (KB-H002)] The attribute 'channel' should not be declared in the recipe. Please, remove it." in output