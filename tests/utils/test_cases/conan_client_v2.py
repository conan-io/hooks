# coding=utf-8

import os
import shutil
import tempfile
import uuid
import subprocess

from tests.utils.environ_vars import context_env


class ConanClientV2TestCase(object):
    """ Helper class to run isolated conan commands """
    _old_cwd = None
    _working_dir = None
    _home = None

    def _get_environ(self, **kwargs):
        kwargs.update({'CONAN_HOME': self._home})
        return kwargs

    @property
    def working_dir(self):
        return self._working_dir

    @property
    def home(self):
        return self._home

    @property
    def hooks_dir(self):
        return os.path.join(self._home, "extensions", "hooks")

    def conan(self, command, expected_return_code=0):
        with context_env(**self._get_environ()):
            result = b""
            try:
                conan_command = str(" ").join(["conan"] + command)
                result = subprocess.check_output(conan_command, shell=True, stderr=subprocess.STDOUT)
                print(result.decode())
            except subprocess.CalledProcessError as error:
                print(error.output.decode())
                assert expected_return_code == error.returncode, "Expected to pass but Conan command failed."
            else:
                assert 0 == expected_return_code, "Conan command passed but expected to fail"
            return result.decode()

    def setup_method(self, method):
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        testcase_dir = os.path.join(self._working_dir, str(uuid.uuid4()))
        test_package_dir = os.path.join(testcase_dir, 'test_package')
        os.makedirs(testcase_dir)
        os.chdir(testcase_dir)
        os.makedirs(test_package_dir)

    @classmethod
    def setup_class(cls):
        cls._working_dir = tempfile.mkdtemp()
        cls._old_cwd = os.getcwd()
        cls._home = os.path.join(cls._working_dir, 'home')

    @classmethod
    def teardown_class(cls):
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