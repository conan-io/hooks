import os
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH008(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import copy
            import os
            class AConan(ConanFile):                
                exports_sources = "*"
                settings = "os", "compiler", "arch", "build_type"
                def configure(self):
                    {configure}
                def package(self):
                    copy(self, pattern="*", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH008, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_header_only_with_cppstd(self):
        save(self, 'src/test.h', content="#define FOO 1")
        save(self, 'src/header.h', content="#define FOO 1")
        save(self, 'conanfile.py', content=self.conanfile.format(configure="pass"))
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [PURE-C MANAGEMENT (KB-H008)] Can't detect C++ source files but recipe does not remove 'self.settings.compiler.libcxx'" in output
        assert "ERROR: [PURE-C MANAGEMENT (KB-H008)] Can't detect C++ source files but recipe does not remove 'self.settings.compiler.cppstd'" in output

    def test_delete_cppstd(self):
        save(self, 'conanfile.py', content=self.conanfile.format(configure="""
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd"""))
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[PURE-C MANAGEMENT (KB-H008)] OK" in output

    def test_remove_safe_cppstd(self):
        save(self, 'conanfile.py', content=self.conanfile.format(configure="""
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")"""))
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[PURE-C MANAGEMENT (KB-H008)] OK" in output

    def test_remove_safe_cppstd_from_compiler(self):
        save(self, 'conanfile.py', content=self.conanfile.format(configure="""
        self.settings.compiler.rm_safe("libcxx")
        self.settings.compiler.rm_safe("cppstd")"""))
        output = self.conan(['create', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "[PURE-C MANAGEMENT (KB-H008)] OK" in output