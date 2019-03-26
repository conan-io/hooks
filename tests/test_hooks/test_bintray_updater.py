#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import textwrap
import responses

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.licenses import OSS_LICENSES

def accept_conan_upload(func):
    """ Decorator to replace remote URLs
    :param func: Wrapped function
    """
    def wrapper(*args, **kwargs):
        empty_package_response = {
            "desc":None,
            "labels":[],
            "licenses":[],
            "website_url":None,
            "issue_tracker_url":None,
            "github_repo":None,
            "vcs_url":None,
            "maturity":""
        }
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/ping')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/digest', json={"conanmanifest.txt":""})
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan', status=404)
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/users/check_credentials')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable', json={})
        responses.add(responses.POST, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/upload_urls', json={})
        responses.add(responses.GET, "https://api.bintray.com/licenses/oss_licenses", json=OSS_LICENSES)
        responses.add(responses.PATCH, "https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar", json={})
        responses.add(responses.GET, 'https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', json=empty_package_response)
        func(*args, **kwargs)
    return wrapper


def add_fake_remote(func):
    """ Decorator that add fake Conan remote
    :param func: Wrapped function
    """
    def wrapper(*args, **kwargs):
        instance = args[0]
        output = instance.conan(['remote', 'list'])
        if 'fake' not in output:
            instance.conan(['remote', 'add', 'fake', 'https://api.bintray.com/conan/foobar/conan'])
        func(*args, **kwargs)
    return wrapper

class BintrayUpdaterEnvironmentTest(ConanClientTestCase):
    """ Execute test without Bintray env vars
    """

    # Empty Recipe
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile
        class DummyConan(ConanFile):
            pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(BintrayUpdaterEnvironmentTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'bintray_updater')})
        return kwargs

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_unset_bintray_credentials(self):
        """ The hook must not work when BINTRAY_USERNAME is not configured
        """
        tools.save('conanfile.py', content=self.conanfile_base)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
        self.assertIn("post_upload_recipe(): ERROR: Could not update Bintray info: username not found", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_unset_bintray_password(self):
        """ The hook must not work when BINTRAY_PASSWORD is not configured
        """
        with tools.environment_append({"BINTRAY_USERNAME": "foobar"}):
            tools.save('conanfile.py', content=self.conanfile_base)
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
            self.assertIn("post_upload_recipe(): ERROR: Could not update Bintray info: password not found", output)

class BintrayUpdaterTest(ConanClientTestCase):
    """ Test the hook with valid credentials
    """

    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class DummyConan(ConanFile):
            {placeholder}
        """)
    conanfile_basic = conanfile_base.format(placeholder='pass')
    conanfile_complete = conanfile_base.format(placeholder="""url = "https://github.com/foobar/conan-dummy"
    description = "This a dummy library"
    homepage = "https://dummy.org"
    topics = ("conan", "dummy", "qux", "baz")
    license = "MIT"
    """)

    def _get_environ(self, **kwargs):
        kwargs = super(BintrayUpdaterTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'bintray_updater'),
                       'BINTRAY_USERNAME': "frogarian",
                       'BINTRAY_PASSWORD': "e91d34eb1c11aafaf44ag2e5194f29690ad6f383"})
        return kwargs

    def tearDown(self):
        self.conan(["remove", "--force", "dummy/0.1.0@foobar/stable"])

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_valid_upload(self):
        """ Regular flow using the hook. Inpect, read, compare and update.
            If this test fails it's because something is REALLY bad.
        """
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
        self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn("post_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc github_repo issue_tracker_url labels licenses vcs_url website_url.", output)
        self.assertIn("post_upload_recipe(): Bintray package information has been updated with success.", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_bad_oss_licenses(self):
        """ Test when is not possible to retrieve the supported OSS license list from Bintray.
            The hook must stop when is not possible to request OSS licenses.
        """
        responses.replace(responses.GET, "https://api.bintray.com/licenses/oss_licenses", status=500, json={"message": "You have reached a dark spot"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake'", output)
        self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn('post_upload_recipe(): ERROR: Could not request OSS licenses (500): {"message": "You have reached a dark spot"}', output)

    @responses.activate
    @accept_conan_upload
    def test_bad_remote_address(self):
        """ Test non Bintray remote address.
            The hooks must not upload when is not a Bintray valid address.
        """
        responses.add(responses.GET, 'https://api.fake.io/v1/ping')
        responses.add(responses.GET, 'https://api.fake.io/v1/conans/dummy/0.1.0/foobar/stable/digest', json={"conanmanifest.txt":""})
        responses.add(responses.GET, 'https://api.fake.io', status=404)
        responses.add(responses.GET, 'https://api.fake.io/v1/users/check_credentials')
        responses.add(responses.GET, 'https://api.fake.io/v1/conans/dummy/0.1.0/foobar/stable', json={})
        responses.add(responses.POST, 'https://api.fake.io/v1/conans/dummy/0.1.0/foobar/stable/upload_urls', json={})
        self.conan(['remote', 'add', 'badremote', 'https://api.fake.io'])
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=badremote', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'badremote'", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'badremote'", output)
        self.assertNotIn("post_upload_recipe(): Reading package info from Bintray.", output)
        self.assertNotIn("post_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn("post_upload_recipe(): ERROR: The remote 'badremote' is not a valid Bintray URL.", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_bad_package_info_request(self):
        """ Test bad request when retrieving package information from Bintray.
            The hook must not continue when is not possible to retrieve the cached information.
        """
        responses.replace(responses.GET, 'https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', status=500, json={"message": "You have reached a dark spot"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
        self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn('ERROR: Could not request package info (500): {"message": "You have reached a dark spot"}', output)
        self.assertNotIn("post_upload_recipe(): Inspecting recipe info.", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_bad_patch_package_info(self):
        """ Test bad request when patching the package information on Bintray.
            The hook must not continue when is not possible to patch the information.
        """
        responses.replace(responses.PATCH, "https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar", status=500, json={"message": "You have reached a dark spot"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
        self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn("post_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc github_repo issue_tracker_url labels licenses vcs_url website_url.", output)
        self.assertIn('post_upload_recipe(): ERROR: Could not patch package info: {"message": "You have reached a dark spot"}', output)
        self.assertNotIn("post_upload_recipe(): Bintray package information has been updated with success.", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_stable_branch(self):
        """ Test the maturity level update.
            The hook must update the maturity level when the branch matches to the stable branch pattern.
        """
        with tools.environment_append({"TRAVIS": "TRUE", "TRAVIS_BRANCH": "release/0.1.0"}):
            tools.save('conanfile.py', content=self.conanfile_complete)
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
            self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
            self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
            self.assertIn("post_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc github_repo issue_tracker_url labels licenses maturity vcs_url website_url.", output)
            self.assertIn("post_upload_recipe(): Bintray package information has been updated with success.", output)
            self.assertNotIn('post_upload_recipe(): ERROR', output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_stable_branch_pattern(self):
        """ Test the maturity level update with custom branch pattern.
            The stable branch pattern can be customized by environment variable.
        """
        with tools.environment_append({"TRAVIS": "TRUE", "TRAVIS_BRANCH": "tag/0.1.0", "CONAN_STABLE_BRANCH_PATTERN": "tag/*"}):
            tools.save('conanfile.py', content=self.conanfile_complete)
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
            self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
            self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
            self.assertIn("post_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc github_repo issue_tracker_url labels licenses maturity vcs_url website_url.", output)
            self.assertIn("post_upload_recipe(): Bintray package information has been updated with success.", output)
            self.assertNotIn('post_upload_recipe(): ERROR', output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_unsafe_url(self):
        """ Check if HTTPS is the only option.
            The hooks must not support HTTP, since Bintray uses Basic Auth.
        """
        empty_package_response = {
            "desc":None,
            "labels":[],
            "licenses":[],
            "website_url":None,
            "issue_tracker_url":None,
            "vcs_url":None,
            "github_repo": None,
            "maturity":""
        }
        responses.add(responses.GET, 'http://api.bintray.com/conan/foobar/conan/v1/ping')
        responses.add(responses.GET, 'http://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/digest', json={"conanmanifest.txt":""})
        responses.add(responses.GET, 'http://api.bintray.com/conan/foobar/conan', status=404)
        responses.add(responses.GET, 'http://api.bintray.com/conan/foobar/conan/v1/users/check_credentials')
        responses.add(responses.GET, 'http://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable', json={})
        responses.add(responses.POST, 'http://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/upload_urls', json={})
        responses.add(responses.GET, "http://api.bintray.com/licenses/oss_licenses", json={})
        responses.add(responses.GET, 'http://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', json=empty_package_response)
        with tools.environment_append({"BINTRAY_API_URL": "http://api.bintray.com"}):
            tools.save('conanfile.py', content=self.conanfile_complete)
            self.conan(['remote', 'add', 'unsafe', 'http://api.bintray.com/conan/foobar/conan'])
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=unsafe', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'unsafe'", output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'unsafe': http://api.bintray.com/conan/foobar/conan", output)
            self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
            self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
            self.assertIn("post_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc github_repo issue_tracker_url labels vcs_url website_url.", output)
            self.assertIn('post_upload_recipe(): ERROR: Bad package URL: Only HTTPS is allowed, Bintray API uses Basic Auth', output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_up_to_date_info(self):
        """ Do not update when the information is up-to-date.
            The hook must not patch when there is no different between local recipe and remote info.
        """
        information = {
            "desc": "This a dummy library",
            "labels":["conan", "dummy", "qux", "baz"],
            "licenses":["MIT"],
            "website_url": "https://dummy.org",
            "issue_tracker_url":"https://github.com/foobar/community/issues",
            "vcs_url":"https://github.com/foobar/conan-dummy",
            "github_repo": "foobar/conan-dummy",
            "maturity":"Stable"
        }
        responses.replace(responses.GET, 'https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', json=information)
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
        self.assertIn("post_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("post_upload_recipe(): Inspecting recipe info.", output)
        self.assertNotIn("post_upload_recipe(): Bintray is outdated.", output)
        self.assertIn("post_upload_recipe(): Bintray package info is up-to-date.", output)
        self.assertNotIn("post_upload_recipe(): Bintray package information has been updated with success.", output)
