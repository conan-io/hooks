import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH032(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conan import ConanFile
        class AConan(ConanFile):
            def requirements(self):
                {placeholder}
                pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH032, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_with_override_true(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="self.requires('package/version', override=True)"))
        output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "ERROR: [REQUIREMENT OVERRIDE PARAMETER (KB-H032)]" in output

    def test_with_override_false(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="self.requires('package/version', override=False)"))
        output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "[REQUIREMENT OVERRIDE PARAMETER (KB-H032)] OK" in output

    def test_with_commented_requires(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="# self.requires('package/version', override=True)"))
        output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "[REQUIREMENT OVERRIDE PARAMETER (KB-H032)] OK" in output

    def test_no_requires(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder=""))
        output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "[REQUIREMENT OVERRIDE PARAMETER (KB-H032)] OK" in output

    def test_with_private_false(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="self.requires('package/version', private=False, override=False)"))
        output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "[REQUIREMENT OVERRIDE PARAMETER (KB-H032)] OK" in output

    def test_with_private_true(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="self.requires('package/version', override=True, private=False)"))
        output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "ERROR: [REQUIREMENT OVERRIDE PARAMETER (KB-H032)]" in output