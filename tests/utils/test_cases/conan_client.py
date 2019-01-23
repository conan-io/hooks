# coding=utf-8

import os
import shutil
import stat
import tempfile
import unittest
from io import StringIO

from conans.client.command import Conan, CommandOutputer, Command, SUCCESS
from tests.utils.environ_vars import context_env


class ConanClientTestCase(unittest.TestCase):
    """ Helper class to run isolated conan commands """

    def _get_environ(self, **kwargs):
        # kwargs = super(ConanClientTestCase, **kwargs)
        home = os.path.join(self._working_dir, 'home')
        home_short = os.path.join(self._working_dir, 'hs')
        kwargs.update({'CONAN_USER_HOME': home, 'CONAN_USER_HOME_SHORT': home_short})
        return kwargs

    def conan(self, command, expected_return_code=SUCCESS):
        with context_env(**self._get_environ()):
            # This snippet reproduces code from conans.client.command.main, we cannot directly
            # use it because in case of error it is exiting the python interpreter :/
            conan_api, cache, user_io = Conan.factory()
            output_stream = StringIO()
            user_io.out._stream = output_stream
            outputer = CommandOutputer(user_io, cache)
            cmd = Command(conan_api, cache, user_io, outputer)
            return_code = cmd.run(command)
            self.assertEqual(return_code, expected_return_code,
                             msg="Unexpected return code\n\n{}".format(output_stream.getvalue()))
            return output_stream.getvalue()

    @classmethod
    def setUpClass(cls):
        cls._working_dir = tempfile.mkdtemp()
        cls._old_cwd = os.getcwd()
        os.chdir(cls._working_dir)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._old_cwd)

        def _change_permissions(func, path, exc_info):
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise OSError(
                    "Cannot change permissions for {}! Exception info: {}".format(path, exc_info))

        shutil.rmtree(cls._working_dir, onerror=_change_permissions)
