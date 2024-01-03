import os
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save
from parameterized import parameterized



class TestKBH013(ConanClientV2TestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH013, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_allowed_files(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile
                    from conan.tools.files import save
                    import os
                    class AConan(ConanFile):
                        def package(self):
                            save(self, os.path.join(self.package_metadata_folder, "foobar.pdb"), content="foobar")
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[METADATA FILES (KB-H013)] OK" in output

    @parameterized.expand([("foo.pdb", ), ("foo.la", ), ("vcruntime12.dll")])
    def test_config_files(self, file):
        conanfile = textwrap.dedent(f"""\
                    from conan import ConanFile
                    from conan.tools.files import save
                    import os
                    class AConan(ConanFile):
                        def package(self):
                            save(self, os.path.join(self.package_folder, "lib", "{file}"), content="foobar")
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [METADATA FILES (KB-H013)] Files" in output