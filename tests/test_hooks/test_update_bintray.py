# coding=utf-8

import os
import textwrap

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase


class BintrayUpdateTests(ConanClientTestCase):
    conanfile_basic = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            name = "foo"
            version = "version"
            description = "virtual recipe"
            license = "MIT"
            author = "Conan Community"
            url = "https://github.com/conan-community/foo"
            homepage = "https://github.com/foo/foo"
            topics = ("conan", "foo", "bar", "qux")
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(BintrayUpdateTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'bintray-update')})
        return kwargs

    def test_conanfile_basic(self):
        tools.save('conanfile.py', content=self.conanfile_basic)
        self.conan(['conan', 'remote', 'add', 'virtual', 'https://api.bintray.com/conan/conan-community/test-distribution'])
        self.conan(['conan', 'export', '.', 'foo/version@bar/test'])
        output = self.conan(['conan', 'upload', '--force', '--remote=virtual','foo/version@bar/test'])
        self.assertIn("Uploading foo/version@bar/test to remote 'virtual'", output)
        self.assertIn("post_upload_recipe(): Reading package info form Bintray", output)
        self.assertIn("post_upload_recipe(): Inspecting recipe info ...", output)
        self.assertIn("post_upload_recipe(): Bintray is outdated. Updating Bintray package info ...", output)
        self.assertNotIn("ERROR", output)
