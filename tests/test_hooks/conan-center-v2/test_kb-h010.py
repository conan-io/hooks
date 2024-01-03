import os
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH010(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import copy
            import os
            class AConan(ConanFile):                
                exports_sources = "*"
                settings = "os", "compiler", "arch", "build_type"                
                def package(self):
                    copy(self, pattern="*", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH010, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_allowed_folders(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile     
                    import os               
                    class AConan(ConanFile):
                        def package(self):
                            for folder in ["licenses", "bin", "include", "lib", "res", "metadata"]:
                                os.makedirs(os.path.join(self.package_folder, folder))
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[DEFAULT PACKAGE LAYOUT (KB-H010)] OK" in output

    def test_unknown_folders(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile     
                    import os               
                    class AConan(ConanFile):
                        def package(self):
                            for folder in ["licenses", "bin", "include", "lib", "res", "metadata", "share", "doc", "build"]:
                                os.makedirs(os.path.join(self.package_folder, folder))
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [DEFAULT PACKAGE LAYOUT (KB-H010)] Unknown folder 'share' in the package" in output
        assert "ERROR: [DEFAULT PACKAGE LAYOUT (KB-H010)] Unknown folder 'doc' in the package" in output
        assert "ERROR: [DEFAULT PACKAGE LAYOUT (KB-H010)] Unknown folder 'build' in the package" in output

    def test_unknown_file(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile     
                    from conan.tools.files import save
                    import os               
                    class AConan(ConanFile):
                        def package(self):
                            save(self, os.path.join(self.package_folder, "foobar.txt"), content="foobar")
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [DEFAULT PACKAGE LAYOUT (KB-H010)] Unknown file 'foobar.txt' in the package" in output
        assert "[DEFAULT PACKAGE LAYOUT (KB-H010)] If you are trying to package a tool put all the contents under the 'bin' folder" in output