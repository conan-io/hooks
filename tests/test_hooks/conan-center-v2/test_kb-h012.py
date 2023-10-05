import os
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save
from parameterized import parameterized



class TestKBH012(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import save
            import os
            class AConan(ConanFile):
                def package(self):
                    save(self, os.path.join(self.package_folder, "lib", "{placeholder}"), content="foobar")
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH012, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_allowed_files(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="libfoo.so"))
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[NOT ALLOWED CONFIG-FILES (KB-H012)] OK" in output

    @parameterized.expand([("FindFoo.cmake", ), ("libfoo.pc", ), ("foo-config.cmake")])
    def test_config_files(self, file):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder=file))
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [NOT ALLOWED CONFIG-FILES (KB-H012)] Found files" in output