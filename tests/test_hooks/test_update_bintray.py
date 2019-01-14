# coding=utf-8

import os
import sys
import re
import textwrap
import json
from mock import mock
from tests.utils.environ_vars import context_env

from conans import tools

from conans.client.remote_registry import Remote
from conans.model.ref import ConanFileReference
from conans.test.utils.tools import TestBufferConanOutput

from tests.utils.test_cases.conan_client import ConanClientTestCase

sys.path.append(os.path.join(os.getenv("TOX_WORK_DIR"), '..', 'hooks'))
import bintray_update


class MockResponse:
    def __init__(self, json_data, status_code, ok=False, text=None):
        self.json_data = json_data
        self.status_code = status_code
        self.ok = ok
        self.text = str(json_data) if not text else text

    def json(self):
        return self.json_data


def side_effect_get(url, *args, **kwargs):
    if url:
        match = re.search(pattern='packages\/(.*)\/(.*)\/(.*)%3A(.*)', string=url)
        if not match:
            return MockResponse(None, 404, text="Invalid URL: {}".format(url))
        response = {
            "name": "{}:{}".format(match.group(3), match.group(4)),
            "repo": match.group(2),
            "owner": match.group(1),
            "desc": "Dummy package",
            "labels": ["conan", "testing", "hooks"],
            "attribute_names": ["maturity"],
            "licenses": ["MIT"],
            "custom_licenses": [],
            "followers_count": 1,
            "created": "2018-02-18T07:13:28.810Z",
            "website_url": "https://github.com/conan-community/foo",
            "issue_tracker_url": "https://github.com/bincrafters/community/issues",
            "linked_to_repos": ["foobar"],
            "permissions": [],
            "versions": ["0.0.0:stable", "0.1.0:stable"],
            "latest_version": "0.1.0:stable",
            "updated": "2018-11-03T01:58:21.801Z",
            "rating_count": 0,
            "system_ids": [],
            "vcs_url": "https://github.com/conan-community/foo",
            "maturity": "Stable"
        }
        return MockResponse(response, 200, True)

    return MockResponse(None, 404, text="URL must be declared")


def side_effect_patch(url, auth, json, *args, **kwargs):
    if auth.username != os.getenv("CONAN_USERNAME") or auth.password != os.getenv("CONAN_PASSWORD"):
        response = {"message": "This resource requires authentication"}
        return MockResponse(response, 401)
    if not json["vcs_url"]:
        response = {"message": "Please enter a valid VCS URL for your package."}
        return MockResponse(response, 400)
    if url:
        response = {"message": "success"}
        return MockResponse(response, 200, True)
    return MockResponse(None, 404)


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
    conanfile_limited = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            name = "foo"
            version = "version"
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(BintrayUpdateTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_USERNAME': 'chespirito', 'CONAN_PASSWORD': 'elchapulincolorado'})
        return kwargs

    @mock.patch('bintray_update.requests.get', side_effect=side_effect_get)
    @mock.patch('bintray_update.requests.patch', side_effect=side_effect_patch)
    def test_conanfile_basic(self, mock_get, mock_patch):
        reference = ConanFileReference.loads("foo/0.1.0@bar/testing")
        remote = Remote(
            name="virtual",
            url="https://api.bintray.com/conan/conan-community/test-distribution",
            verify_ssl=True)
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = TestBufferConanOutput()

        with context_env(**self._get_environ()):
            bintray_update.post_upload_recipe(
                output=output, conanfile_path='conanfile.py', reference=reference, remote=remote)

            self.assertIn("Reading package info form Bintray", output)
            self.assertIn("Inspecting recipe info ...", output)
            self.assertIn("Bintray is outdated. Updating Bintray package info: desc labels vcs_url issue_tracker_url website_url", output)
            self.assertNotIn("ERROR", output)

    @mock.patch('bintray_update.requests.get', side_effect=side_effect_get)
    @mock.patch('bintray_update.requests.patch', side_effect=side_effect_patch)
    def test_conanfile_unfilled(self, mock_get, mock_patch):
        reference = ConanFileReference.loads("foo/0.1.0@bar/testing")
        remote = Remote(
            name="virtual",
            url="https://api.bintray.com/conan/conan-community/test-distribution",
            verify_ssl=True)
        tools.save('conanfile.py', content=self.conanfile_limited)
        output = TestBufferConanOutput()

        with context_env(**self._get_environ()):
            bintray_update.post_upload_recipe(
                output=output, conanfile_path='conanfile.py', reference=reference, remote=remote)

            self.assertIn("Reading package info form Bintray", output)
            self.assertIn("Inspecting recipe info ...", output)
            self.assertIn("Bintray package info is up-to-date.", output)
            self.assertNotIn("ERROR", output)

    def test_bad_remote(self):
        url = "https://foo.bar/conan/test-distribution"
        reference = ConanFileReference.loads("foo/0.1.0@bar/testing")
        remote = Remote(
            name="virtual",
            url=url,
            verify_ssl=True)
        tools.save('conanfile.py', content=self.conanfile_limited)
        output = TestBufferConanOutput()

        with context_env(**self._get_environ()):
            bintray_update.post_upload_recipe(
                output=output, conanfile_path='conanfile.py', reference=reference, remote=remote)

            self.assertIn("ERROR", output)
            self.assertIn("Could not extract subject and repo from {}: Invalid pattern".format(url), output)

    def test_bad_login(self):
        reference = ConanFileReference.loads("foo/0.1.0@bar/testing")
        remote = Remote(
            name="virtual",
            url="https://api.bintray.com/conan/conan-community/test-distribution",
            verify_ssl=True)
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = TestBufferConanOutput()

        env = self._get_environ()
        del env["CONAN_USERNAME"]

        with context_env(**env):
            bintray_update.post_upload_recipe(
                output=output, conanfile_path='conanfile.py', reference=reference, remote=remote)

            self.assertIn("ERROR", output)
            self.assertIn("Could not update Bintray info: username not found", output)

    @mock.patch('bintray_update.requests.get', return_value=MockResponse(None, 500, False, "Internal Server Error"))
    def test_bad_server_response(self, mock_get):
        reference = ConanFileReference.loads("foo/0.1.0@bar/testing")
        remote = Remote(
            name="virtual",
            url="https://api.bintray.com/conan/conan-community/test-distribution",
            verify_ssl=True)
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = TestBufferConanOutput()

        with context_env(**self._get_environ()):
            bintray_update.post_upload_recipe(
                output=output, conanfile_path='conanfile.py', reference=reference, remote=remote)

            self.assertIn("ERROR", output)
            self.assertIn("Could not request package info: Internal Server Error (500)", output)
