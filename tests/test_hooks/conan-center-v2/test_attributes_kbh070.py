import os
import shutil
import textwrap

from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class SettingsAttrTests(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conan import ConanFile

        class AConan(ConanFile):
           {}
           pass

        """)

    def _get_environ(self, **kwargs):
        kwargs = super(SettingsAttrTests, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan-center-v2.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan-center-v2.py')
            shutil.copy2(hook_path, self.hooks_dir)
        print(f"****** HOOKS DIR: {self.hooks_dir}")
        return kwargs

    def test_with_settings(self):
        save(SettingsAttrTests, 'conanfile.py', content=self.conanfile.replace("{}", "settings = 'os', 'arch', 'compiler', 'build_type'"))
        output = self.conan(['config', 'home'])
        print(f"************** CONAN HOME: {output}")

        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])

        self.assertNotIn("WARN: [MANDATORY SETTINGS (KB-H070)]", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)

    def test_without_settings(self):
        save(SettingsAttrTests, 'conanfile.py', content=self.conanfile)
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        self.assertIn("WARN: [MANDATORY SETTINGS (KB-H070)] "
                      "No 'settings' detected in your conanfile.py. "
                      "Add 'settings' attribute and use 'package_id(self)' method to manage the package ID.", output)

    def test_missing_settings_values(self):
        save(SettingsAttrTests, 'conanfile.py', content=self.conanfile.replace("{}", "settings = 'os'"))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        self.assertIn("WARN: [MANDATORY SETTINGS (KB-H070)] The values 'arch', 'compiler', 'build_type' are missing on "
                      "'settings' attribute. Update settings with the missing values and use 'package_id(self)' method "
                      "to manage the package ID.", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)

    def test_missing_settings_single_value(self):
        save(SettingsAttrTests, 'conanfile.py', content=self.conanfile.replace("{}", "settings = 'os', 'arch', 'build_type'"))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        self.assertIn("WARN: [MANDATORY SETTINGS (KB-H070)] The values 'compiler' are missing on "
                      "'settings' attribute. Update settings with the missing values and use 'package_id(self)' method "
                      "to manage the package ID.", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)
