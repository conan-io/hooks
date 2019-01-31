# coding=utf-8

"""
Export metadata
---------------

This hook generates a dictionary with the repository data where the conanfile.py resides,
stores it in a file and exports it with the recipe. It is executed in the `export` command:

    $ conan export . package/0.1.0@user/channel
    [HOOK - /Users/jgsogo/dev/conan/conan-hooks/tests/test_hooks/../../hooks/export_metadata.py] pre_export(): Exported metadata to file 'metadata.json'
    Exporting package recipe
    name/version@jgsogo/test exports: Copied 1 '.json' file: metadata.json
    name/version@jgsogo/test: A new conanfile.py version was exported

This information could be retrieved using the command `get`

    $ conan get package/0.1.0@user/channel metadata.json


Note.- The default filename is 'metadata.json', although the user can change it using the
environment variable 'CONAN_HOOK_METADATA_FILENAME'

"""

import json
import os
import sys

import semver

from conans import __version__
from conans.errors import ConanException
from conans.tools import Git, save, SVN

_CONAN_HOOK_METADATA_FILENAME_ENV_VAR = 'CONAN_HOOK_METADATA_FILENAME'
CONAN_HOOK_METADATA_FILENAME = 'metadata.json'


def _try_repo_data(path, repo_class):
    repo = repo_class(path)
    try:
        kwargs = {}
        if not semver.satisfies(__version__, "<=1.12.x", loose=True):
            kwargs.update({'remove_credentials': True})
        return {'type': repo_class.cmd_command,
                'url': repo.get_remote_url(**kwargs),
                'revision': repo.get_revision(),
                'dirty': bool(not repo.is_pristine())}
    except ConanException:
        pass
    except Exception as e:
        sys.stderr.write("Unhandled error using '{}': {}".format(repo_class, e))


def pre_export(output, conanfile, conanfile_path, *args, **kwargs):
    """ Grab some meta-information from the local folder, write it to a file
        and upload it within the recipe
    """
    # Check that we are not overriding any file
    filename = os.getenv(_CONAN_HOOK_METADATA_FILENAME_ENV_VAR, CONAN_HOOK_METADATA_FILENAME)
    target_path = os.path.join(os.path.dirname(conanfile_path), filename)
    if os.path.exists(target_path):
        output.error("Target file to write metadata already exists: '{}'. Use"
                     " environment variable '{}' to set a different filename".
                     format(target_path, _CONAN_HOOK_METADATA_FILENAME_ENV_VAR))
        return

    # Look for the repo
    path = os.path.dirname(conanfile_path)
    scm_data = _try_repo_data(path, Git) or _try_repo_data(path, SVN)
    if not scm_data:
        output.warn("Cannot identify a repository system in "
                    "directory '{}' (tried SVN and Git)".format(path))
        return

    # Dump information to file and export it with the recipe
    content = json.dumps(scm_data)
    save(target_path, content)
    if not getattr(conanfile, 'exports'):
        setattr(conanfile, 'exports', os.path.basename(filename))
    else:
        conanfile.exports = conanfile.exports, os.path.basename(filename)
    output.info("Exported metadata to file '{}'".format(filename))
