import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH028(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                from conan import ConanFile
                class AConan(ConanFile):
                    exports = "foo."
                """)
    conanfile_long = textwrap.dedent("""\
                from conan import ConanFile
                from conan.tools.files import mkdir, save
                import os
                class AConan(ConanFile):
                    # short_paths = True
                    def package(self):
                        includedir = os.path.join(self.package_folder, "include", "another-include-folder", "another-subfolder")
                        mkdir(self, includedir)
                        save(self, os.path.join(includedir, "a-very-very-very-long-header-file-which-may-trigger-hook-66.h"), "")
                """)
    conanfile_source = textwrap.dedent("""\
                from conan import ConanFile
                from conan.tools.files import mkdir, save
                import os
                class AConan(ConanFile):
                    no_copy_source = True
                    # short_paths = True
                    def source(self):
                        includedir = os.path.join(self.source_folder, "include", "another-include-folder", "another-subfolder", "very-very-very-long-folder-subfolder"  )
                        mkdir(self, includedir)
                        save(self, os.path.join(includedir, "a-very-very-very-long-header-file-which-may-trigger-hook-66.h"), "")
                """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH028, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def setup_method(self, method):
        self.conan(['profile', 'detect', '--force'])

    def test_include_folder(self):
        save(self, 'conanfile.py', content=self.conanfile_long)
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [SHORT_PATHS USAGE (KB-H028)] The file" in output

    def test_include_folder_short_paths(self):
        save(self, 'conanfile.py', content=self.conanfile_long.replace("# s", "s"))
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [SHORT_PATHS USAGE (KB-H028)]" not in output
        assert "[SHORT_PATHS USAGE (KB-H028)] OK" in output

    def test_source_folder_long_path(self):
        save(self, 'conanfile.py', content=self.conanfile_source)
        output = self.conan(['create', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "WARN: [SHORT_PATHS USAGE (KB-H028)] The file" in output