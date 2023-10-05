import os
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH009(ConanClientV2TestCase):
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
        kwargs = super(TestKBH009, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def setup_method(self, method):
        self.conan(['profile', 'detect', '--force'])

    def test_no_license_folder(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile                    
                    class AConan(ConanFile):
                        pass
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [PACKAGE LICENSE (KB-H009)] No 'licenses' folder found in package folder" in output

    def test_no_license_file(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile
                    import os
                    class AConan(ConanFile):
                        def package(self):
                            os.makedirs(os.path.join(self.package_folder, "licenses"))
                    """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [PACKAGE LICENSE (KB-H009)] No license files found in the license folder" in output

    def test_license_file_empty(self):
        conanfile = textwrap.dedent("""\
                            from conan import ConanFile
                            from conan.tools.files import save
                            import os
                            class AConan(ConanFile):
                                def package(self):                                
                                    save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), content="")                                    
                            """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [PACKAGE LICENSE (KB-H009)] Empty license file found" in output

    def test_license_file_ok(self):
        conanfile = textwrap.dedent("""\
                            from conan import ConanFile
                            from conan.tools.files import save
                            import os
                            class AConan(ConanFile):
                                def package(self):                                
                                    save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), content="whatever")                                    
                            """)
        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[PACKAGE LICENSE (KB-H009)] OK" in output