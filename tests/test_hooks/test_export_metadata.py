# coding=utf-8

import json
import os
import subprocess
import sys
import textwrap
import unittest

import six
from parameterized import parameterized
from six.moves.urllib.parse import quote

from conans import tools
from conans.paths import CONAN_MANIFEST
from tests.utils import capabilities
from tests.utils.test_cases.conan_client import ConanClientTestCase

here = os.path.dirname(__file__)


def get_export_metadata_vars():
    sys.path.insert(0, os.path.join(here, '..', '..', 'hooks'))
    try:
        from export_metadata import CONAN_HOOK_METADATA_FILENAME, \
            _CONAN_HOOK_METADATA_FILENAME_ENV_VAR
        return CONAN_HOOK_METADATA_FILENAME, _CONAN_HOOK_METADATA_FILENAME_ENV_VAR
    finally:
        sys.path.pop(0)


METADATA_FILENAME, METADATA_FILENAME_ENV_VAR = get_export_metadata_vars()


class ExportMetadataTests(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            {exports}
            pass
        """)
    conanfile_plain = conanfile_base.format(exports="")
    conanfile_with_exports = conanfile_base.format(exports='"myfile.txt"')

    def _get_environ(self, **kwargs):
        kwargs = super(ExportMetadataTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(here, '..', '..', 'hooks', 'export_metadata')})
        return kwargs

    def test_no_repo(self):
        tools.save('conanfile.py', content=self.conanfile_plain)
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn("pre_export(): WARN: Cannot identify a repository system in directory", output)

    def test_conflicting_file(self):
        tools.save('conanfile.py', content=self.conanfile_plain)
        tools.save(METADATA_FILENAME, content='whatever')
        output = self.conan(['export', '.', 'name/version@jgsogo/test'])
        self.assertIn("ERROR: Target file to write metadata already exists", output)
        self.assertIn("Use environment variable '{}' to set a different "
                      "filename".format(METADATA_FILENAME_ENV_VAR), output)

        with tools.environment_append({METADATA_FILENAME_ENV_VAR: "other.json"}):
            output = self.conan(['export', '.', 'name/version@jgsogo/test'])
            self.assertNotIn("ERROR: Target file to write metadata already exists", output)

    @parameterized.expand([(True,), (False,)])
    def test_git_repository(self, with_exports):
        conanfile = self.conanfile_with_exports if with_exports else self.conanfile_plain
        reference = 'name/version@jgsogo/test'
        url = 'http://some.url'

        git = tools.Git()
        git.run("init .")
        git.run('config user.email "you@example.com"')
        git.run('config user.name "Your Name"')
        tools.save('conanfile.py', content=conanfile)
        git.run('add --all')
        git.run('commit -am "initial"')
        git.run('remote add origin {}'.format(url))

        output = self.conan(['export', '.', reference])
        self.assertIn("pre_export(): Exported metadata to file '{}'".format(METADATA_FILENAME),
                      output)

        # Check that the file is in the export folder, contains expected data and is in the manifest
        output = self.conan(['get', reference, METADATA_FILENAME])
        data = json.loads(output)
        self.assertDictEqual(data, {'type': 'git',
                                    'url': url,
                                    'revision': git.get_commit(),
                                    'dirty': False})
        output = self.conan(['get', reference, CONAN_MANIFEST])
        self.assertIn(METADATA_FILENAME, output)

    @parameterized.expand([(True,), (False,)])
    @unittest.skipUnless(capabilities.svn(), "SVN not available")
    def test_svn_repository(self, pristine_repo):
        if pristine_repo and not bool(tools.SVN.get_version() >= tools.SVN.API_CHANGE_VERSION):
            raise unittest.SkipTest("Required SVN >= {} to test for pristine "
                                    "repo".format(tools.SVN.API_CHANGE_VERSION))

        reference = 'name/version@jgsogo/test'

        # Create the SVN repo
        repo_url = self._gimme_tmp()
        subprocess.check_output('svnadmin create "{}"'.format(repo_url), shell=True)
        repo_url = tools.SVN.file_protocol + quote(repo_url.replace("\\", "/"), safe='/:')

        # Create the working repo
        svn = tools.SVN()
        svn.checkout(url=repo_url)
        tools.save('conanfile.py', content=self.conanfile_plain)
        svn.run("add conanfile.py")
        svn.run('commit -m "initial"')
        if pristine_repo:
            svn.run('update')
        self.assertEqual(svn.is_pristine(), pristine_repo)

        output = self.conan(['export', '.', reference])
        self.assertIn("pre_export(): Exported metadata to file '{}'".format(METADATA_FILENAME),
                      output)

        # Check that the file is in the export folder, contains expected data and is in the manifest
        output = self.conan(['get', reference, METADATA_FILENAME])
        data = json.loads(output)
        self.assertListEqual(sorted(data.keys()),
                             sorted([six.u('type'), six.u('url'),
                                     six.u('revision'), six.u('dirty')]))
        self.assertEqual(data['type'], six.u('svn'))
        self.assertEqual(data['url'].lower(), six.u(repo_url).lower())
        self.assertEqual(data['revision'], six.u(svn.get_revision()))
        self.assertEqual(data['dirty'], bool(not pristine_repo))

        output = self.conan(['get', reference, CONAN_MANIFEST])
        self.assertIn(METADATA_FILENAME, output)
