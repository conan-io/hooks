import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class SettingsAttrTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):
           {}
           pass
 
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(SettingsAttrTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_with_settings(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "settings = 'os', 'arch', 'compiler', 'build_type'"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [MANDATORY SETTINGS (KB-H070)]", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)

    def test_without_settings(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [MANDATORY SETTINGS (KB-H070)] "
                      "No 'settings' detected in your conanfile.py. "
                      "Add 'settings' attribute and use 'package_id(self)' method to manage the package ID.", output)

    def test_missing_settings_values(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "settings = 'os'"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [MANDATORY SETTINGS (KB-H070)] The values 'arch', 'compiler', 'build_type' are missing on "
                      "'settings' attribute. Update settings with the missing values and use 'package_id(self)' method "
                      "to manage the package ID.", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)
    
    def test_missing_settings_values_application_skipped(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "package_type = 'application'\n   settings = 'os'"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [MANDATORY SETTINGS (KB-H070)] The values 'arch', 'compiler', 'build_type' are missing on "
                      "'settings' attribute. Update settings with the missing values and use 'package_id(self)' method "
                      "to manage the package ID.", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)

    def test_missing_settings_single_value(self):
        tools.save('conanfile.py', content=self.conanfile.replace("{}", "settings = 'os', 'arch', 'build_type'"))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [MANDATORY SETTINGS (KB-H070)] The values 'compiler' are missing on "
                      "'settings' attribute. Update settings with the missing values and use 'package_id(self)' method "
                      "to manage the package ID.", output)
        self.assertIn("[MANDATORY SETTINGS (KB-H070)] OK", output)
