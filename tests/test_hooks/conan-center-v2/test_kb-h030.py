import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH030(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conan import ConanFile
        class AConan(ConanFile):
            {placeholder}
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH030, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_missing_settings_values(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="settings = 'os'"))
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [MANDATORY SETTINGS (KB-H030)] The values '['arch', 'compiler', 'build_type']' are missing on 'settings' attribute" in output
        assert "[MANDATORY SETTINGS (KB-H030)] OK" in output

    def test_missing_settings_single_value(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="settings = 'os', 'arch', 'build_type'"))
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [MANDATORY SETTINGS (KB-H030)] The values '['compiler']' are missing on 'settings' attribute" in output
        assert "[MANDATORY SETTINGS (KB-H030)] OK" in output