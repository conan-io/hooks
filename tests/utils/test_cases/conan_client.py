# coding=utf-8

import os
import shutil
import tempfile
import unittest
import uuid
from io import StringIO

from conans.client.command import SUCCESS
from tests.utils.conan_command import conan_command
from tests.utils.environ_vars import context_env


class ConanClientTestCase(unittest.TestCase):
    """ Helper class to run isolated conan commands """
    _old_cwd = None
    _working_dir = None

    def _get_environ(self, **kwargs):
        # kwargs = super(ConanClientTestCase, **kwargs)
        home = os.path.join(self._working_dir, 'home')
        home_short = os.path.join(self._working_dir, 'hs')
        kwargs.update({'CONAN_USER_HOME': home, 'CONAN_USER_HOME_SHORT': home_short})
        return kwargs

    def conan(self, command, expected_return_code=SUCCESS):
        with context_env(**self._get_environ()):
            stream = StringIO()
            with conan_command(stream) as cmd:
                try:
                    return_code = cmd.run(command)
                except Exception as e:
                    # Conan execution failed
                    self.fail("Conan execution for this test failed with {}: {}".format(type(e), e))
                else:
                    # Check return code
                    self.assertEqual(return_code, expected_return_code,
                                     msg="Unexpected return code\n\n{}".format(stream.getvalue()))
            return stream.getvalue()

    def setUp(self):
        testcase_dir = os.path.join(self._working_dir, str(uuid.uuid4()))
        os.makedirs(testcase_dir)
        os.chdir(testcase_dir)

    @classmethod
    def setUpClass(cls):
        cls._working_dir = tempfile.mkdtemp()
        cls._old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._old_cwd)

        def handleRemoveReadonly(func, path, exc):
            import errno, stat
            excvalue = exc[1]
            if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
                os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
                func(path)
            else:
                raise Exception("Failed to remove '{}'".format(path))

        shutil.rmtree(cls._working_dir, onerror=handleRemoveReadonly)

    def _gimme_tmp(self):
        return os.path.join(self._working_dir, str(uuid.uuid4()))
