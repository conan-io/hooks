import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ConandataPatchesTestCase(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            exports_sources = ['patches/*']
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(ConandataPatchesTestCase, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_hook_working(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('patches/my.patch', content="")
        tools.save('patches/other.patch', content="")
        tools.save('conandata.yml', content=textwrap.dedent("""
            patches:
              "version":
                 - patch_file: "patches/my.patch"
                   base_path: "source_folder"
              "other":
                 - patch_file: "patches/my.patch"
                   base_path: "source_folder"
                 - patch_file: "patches/other.patch"
                   base_path: "source_folder"
        """))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("exports_sources: Copied 2 '.patch' files: my.patch, other.patch", output)
        self.assertIn("post_export(): [CONANDATA EXPORTED PATCHES (KB-H049)] Remove exported patch 'other.patch',"
                      " it doesn't belong to this version", output)
        self.assertIn("Exported revision: 203c6faa9e0b4b05bca0bf43170c82f9", output)

        # If we add more files, the revision is the same
        tools.save('patches/another.patch', content="")
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("exports_sources: Copied 3 '.patch' files: my.patch, another.patch, other.patch", output)
        self.assertIn("Exported revision: 203c6faa9e0b4b05bca0bf43170c82f9", output)


    def test_patches_not_listed(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content="")
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("post_export(): ERROR: [CONANDATA EXPORTED PATCHES (KB-H049)] The recipe is exporting 'patches'"
                      " but they are not listed in the 'conandata.yml' file", output)

    def test_patches_not_dict(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content=textwrap.dedent("""
            patches:
              "version":
                 patch_file: "patches/0001-build-Fix-build-errors-with-MSVC.patch"
                 base_path: "source_folder"
        """))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("post_export(): ERROR: [CONANDATA EXPORTED PATCHES (KB-H049)] Patches listed in 'conandata.yml'"
                      " for a version should be a list of dicts", output)

    def test_patches_nothing_exported(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content=textwrap.dedent("""
            patches:
              "version":
                 - patch_file: "patches/0001-build-Fix-build-errors-with-MSVC.patch"
                   base_path: "source_folder"
        """))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("post_export(): ERROR: [CONANDATA EXPORTED PATCHES (KB-H049)] Nothing is exported to 'patches'"
                      " although the recipe is exporting them", output)

    def test_patches_not_exported(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('patches/fix.patch', content="")
        tools.save('conandata.yml', content=textwrap.dedent("""
            patches:
              "version":
                 - patch_file: "patches/other.patch"
                   base_path: "source_folder"
        """))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("post_export(): ERROR: [CONANDATA EXPORTED PATCHES (KB-H049)] Listed patch 'other.patch' in"
                      " 'conandata.yml' is not exported from the recipe 'exports_sources' method", output)
