# coding=utf-8

import os
import shutil
import tempfile
import unittest
import uuid
from io import StringIO

from conans.client.command import Conan, CommandOutputer, Command, SUCCESS
from tests.utils.environ_vars import context_env


class ConanClientTestCase(unittest.TestCase):
    """ Helper class to run isolated conan commands """
    _old_cwd = None
    _working_dir = None
    _user_subdir = 'dev'

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
            try:
                return_code = cmd.run(command)
            except Exception as e:
                # Conan execution failed
                self.fail("Conan execution for this test failed with {}: {}".format(type(e), e))
            else:
                # Check return code
                self.assertEqual(return_code, expected_return_code,
                                 msg="Unexpected return code\n\n{}".format(output_stream.getvalue()))
            finally:
                conan_api._remote_manager._auth_manager._localdb.connection.close()  # Close sqlite3
            return output_stream.getvalue()

    def setUp(self):
        user_working_dir = os.path.join(self._working_dir, self._user_subdir)
        os.makedirs(user_working_dir)
        os.chdir(user_working_dir)

    def tearDown(self):
        # Clean working directory
        shutil.rmtree(os.path.join(self._working_dir, self._user_subdir))

    @classmethod
    def setUpClass(cls):
        cls._working_dir = tempfile.mkdtemp()
        cls._old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._old_cwd)
        shutil.rmtree(cls._working_dir)

    def _gimme_tmp(self):
        return os.path.join(self._working_dir, str(uuid.uuid4()))
