# coding=utf-8

import os
import textwrap

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase


def _create_hook(tempfolder, hook_filename, value):
    utils_file = textwrap.dedent("""
        def get_number():
            return {}
    """.format(value))

    hook_file = textwrap.dedent("""
        from utils import get_number

        def pre_export(output, conanfile, *args, **kwargs):
            output.info(">>>> {}")
            output.info(">>>> {{}}".format(get_number()))
    """.format(hook_filename))

    tools.save(os.path.join(tempfolder, hook_filename + '.py'), hook_file)
    tools.save(os.path.join(tempfolder, "utils.py"), utils_file)

    return os.path.join(tempfolder, hook_filename)


class CollidingFilesInRootTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            pass
        """)

    def _get_environ(self, **kwargs):
        hook1 = _create_hook(self._gimme_tmp(), "hook1", "42")
        hook2 = _create_hook(self._gimme_tmp(), "hook2", "23")

        kwargs = super(CollidingFilesInRootTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': ','.join([hook1, hook2, ])})
        return kwargs

    def test_colliding_files(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])

        self.assertIn(">>>> hook1", output)
        self.assertIn(">>>> 42", output)

        self.assertIn(">>>> hook2", output)
        self.assertIn(">>>> 23", output)

