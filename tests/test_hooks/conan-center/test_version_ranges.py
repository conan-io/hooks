# coding=utf-8

import os
import textwrap
import unittest

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase

here = os.path.dirname(__file__)


class VersionRanges(ConanClientTestCase):
    conanfile_match_conf = textwrap.dedent("""
        from conans import ConanFile

        class AConan(ConanFile):
            requires = "name/version@user/channel"  # Do not use name/[>=1.0]@user/channel
    """)

    def _get_environ(self, **kwargs):
        kwargs = super(VersionRanges, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(here, '..', '..', '..', 'hooks', 'conan-center')})
        return kwargs

    def test_no_version_ranges(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile

            class AConan(ConanFile):
                requires = "name/version@user/channel"  # Do not use name/[>=1.0]@user/channel
                # Because version ranges in comments are not used: name/[>=1.0]@user/channel
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertNotIn("Possible use of version ranges", output)

    def test_version_ranges(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile

            class AConan(ConanFile):
                requires = "name/[>=1]@user/channel"
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn("Possible use of version ranges", output)

    def test_version_ranges2(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile

            class AConan(ConanFile):
                def requirements(self):
                    self.requires('name/[>=1,2.0, include_prerelease=True]@user/channel')
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn("Possible use of version ranges", output)

    @unittest.expectedFailure
    def test_string_in_comment(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile

            class AConan(ConanFile):
                # Although it is commented... "name/[>=1.0]@user/channel"
                requires = "name/version@user/channel"
                
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn("Possible use of version ranges", output)

