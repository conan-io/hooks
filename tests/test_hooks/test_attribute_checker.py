# coding=utf-8

import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase

from tests.utils.compat import save
from tests.utils.compat import v2


class AttributeCheckerTests(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        try:
            from conans import ConanFile
        except ImportError:
            from conan import ConanFile

        class AConan(ConanFile):
            {placeholder}
        """)
    conanfile_basic = conanfile_base.format(placeholder='pass')
    conanfile_alias = conanfile_base.format(placeholder='alias = "something"')

    def _get_environ(self, **kwargs):
        kwargs = super(AttributeCheckerTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'attribute_checker')})
        return kwargs

    def test_conanfile_basic(self):
        save('conanfile.py', content=self.conanfile_basic)
        if v2:
            output = self.conan(['export', '--name', 'name', '--version', 'version', '--user',
                                 'jgsogo', '--channel', 'test', '.'])
        else:
            output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn("pre_export(): WARN: Conanfile doesn't have 'url'", output)
        self.assertIn("pre_export(): WARN: Conanfile doesn't have 'license'", output)
        self.assertIn("pre_export(): WARN: Conanfile doesn't have 'description'", output)

    def test_conanfile_alias(self):
        save('conanfile.py', content=self.conanfile_alias)
        if v2:
            output = self.conan(['export', '--name', 'name', '--version', 'version', '--user',
                                 'jgsogo', '--channel', 'test', '.'])
        else:
            output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertNotIn("pre_export(): WARN: Conanfile doesn't have 'url'", output)
        self.assertNotIn("pre_export(): WARN: Conanfile doesn't have 'license'", output)
        self.assertNotIn("pre_export(): WARN: Conanfile doesn't have 'description'", output)
