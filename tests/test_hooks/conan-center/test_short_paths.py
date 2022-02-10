import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ShortPathsTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            pass
        """)

    conanfile_long = textwrap.dedent("""\
            from conans import ConanFile, tools
            import os
            class AConan(ConanFile):
                # short_paths = True
                def package(self):
                    includedir = os.path.join(self.package_folder, "include", "another-include-folder", "another-subfolder")
                    tools.mkdir(includedir)
                    tools.save(os.path.join(includedir, "a-very-very-very-long-header-file-which-may-trigger-hook-66.h"), "")
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(ShortPathsTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_not_needed_short_path(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [SHORT_PATHS USAGE (KB-H066)]", output)
        self.assertIn("[SHORT_PATHS USAGE (KB-H066)] OK", output)

    def test_long_package_name(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'a-very-very-long-package-name/version@user/channel'])
        self.assertIn("WARN: [SHORT_PATHS USAGE (KB-H066)] The package name 'a-very-very-long-package-name' "
                      "is too long and may exceed Windows max path length. Add 'short_paths = True' in your recipe.",
                      output)

    def test_long_package_name_with_short_paths(self):
        tools.save('conanfile.py', content=self.conanfile.replace("pass", "short_paths = True"))
        output = self.conan(['create', '.', 'a-very-very-long-package-name/version@user/channel'])
        self.assertNotIn("WARN: [SHORT_PATHS USAGE (KB-H066)]", output)
        self.assertIn("[SHORT_PATHS USAGE (KB-H066)] OK", output)

    def test_include_folder(self):
        tools.save('conanfile.py', content=self.conanfile_long)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [SHORT_PATHS USAGE (KB-H066)] The header file './include/another-include-folder/another-subfolder/a-very-very-very-long-header-file-which-may-trigger-hook-66.h'"
                      " has a very long path and may exceed Windows max path length. Add 'short_paths = True' in your "
                      "recipe.", output)

    def test_include_folder_short_paths(self):
        tools.save('conanfile.py', content=self.conanfile_long.replace("# s", "s"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("WARN: [SHORT_PATHS USAGE (KB-H066)]", output)

    def test_both_long_name_and_path(self):
        tools.save('conanfile.py', content=self.conanfile_long)
        output = self.conan(['create', '.', 'a-very-very-long-package-name/version@user/channel'])
        self.assertIn("WARN: [SHORT_PATHS USAGE (KB-H066)] The package name 'a-very-very-long-package-name' "
                      "is too long and may exceed Windows max path length. Add 'short_paths = True' in your recipe.",
                      output)
        self.assertIn("WARN: [SHORT_PATHS USAGE (KB-H066)] The header file './include/another-include-folder/another-subfolder/a-very-very-very-long-header-file-which-may-trigger-hook-66.h'"
                      " has a very long path and may exceed Windows max path length. Add 'short_paths = True' in your "
                      "recipe.", output)

    def test_both_long_name_and_path_with_shorts_path(self):
        tools.save('conanfile.py', content=self.conanfile_long.replace("# s", "s"))
        output = self.conan(['create', '.', 'a-very-very-long-package-name/version@user/channel'])
        self.assertNotIn("WARN: [SHORT_PATHS USAGE (KB-H066)]", output)
