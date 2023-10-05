import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH026(ConanClientV2TestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH026, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_os_rename_warning(self):
        conanfile = textwrap.dedent("""\
        from conan import ConanFile
        import os
        class AConan(ConanFile):
            def source(self):
                open("foobar.txt", "w")
                os.rename("foobar.txt", "foo.txt")
        """)
        conanfile_tp = textwrap.dedent("""\
        from conan import ConanFile
        import os
        class TestConan(ConanFile):
            def test(self):
                open("foo.txt", "w")
                os.rename("foo.txt", "bar.txt")
        """)

        save(self, 'conanfile.py', content=conanfile)
        save(self, 'test_package/conanfile.py', content=conanfile_tp)

        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [TOOLS RENAME (KB-H026)] The 'os.rename' in conanfile.py may cause permission error on Windows. Use 'conan.tools.files.rename(self, src, dst)' instead." in output
        assert "WARN: [TOOLS RENAME (KB-H026)] The 'os.rename' in test_package/conanfile.py may cause permission error on Windows. Use 'conan.tools.files.rename(self, src, dst)' instead." in output

        save(self, 'conanfile.py', content=conanfile.replace("os.", "tools."))
        save(self, 'test_package/conanfile.py', content=conanfile_tp.replace("os.", "tools."))
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [TOOLS RENAME (KB-H026)] The 'tools.rename' in conanfile.py is outdated and may cause permission error on Windows. Use 'conan.tools.files.rename(self, src, dst)' instead." in output
        assert "WARN: [TOOLS RENAME (KB-H026)] The 'tools.rename' in test_package/conanfile.py is outdated and may cause permission error on Windows. Use 'conan.tools.files.rename(self, src, dst)' instead." in output
        assert "[TOOLS RENAME (KB-H026)] OK" in output

        save(self, 'conanfile.py', content=conanfile.replace("os.rename(", "tools.rename(self, "))
        save(self, 'test_package/conanfile.py', content=conanfile_tp.replace("os.rename(", "tools.rename(self, "))
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [TOOLS RENAME (KB-H026)]" not in output
        assert "[TOOLS RENAME (KB-H026)] OK" in output