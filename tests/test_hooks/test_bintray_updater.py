#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import textwrap
import responses

from conans import tools
from conans.client.command import ERROR_GENERAL
from tests.utils.test_cases.conan_client import ConanClientTestCase


def accept_conan_upload(func):
    def wrapper(*args, **kwargs):
        empty_package_response = {
            "desc":None,
            "labels":[],
            "licenses":[],
            "website_url":None,
            "issue_tracker_url":None,
            "vcs_url":None,
            "maturity":""
        }
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/ping')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/digest', json={"conanmanifest.txt":""})
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan', status=404)
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/users/check_credentials')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable', json={})
        responses.add(responses.POST, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/upload_urls', json={})
        responses.add_passthru("https://api.bintray.com/licenses/oss_licenses")
        responses.add(responses.PATCH, "https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar", json={})
        responses.add(responses.GET, 'https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', json=empty_package_response)
        func(*args, **kwargs)
    return wrapper


def add_fake_remote(func):
    def wrapper(*args, **kwargs):
        instance = args[0]
        output = instance.conan(['remote', 'list'])
        if 'fake' not in output:
            instance.conan(['remote', 'add', 'fake', 'https://api.bintray.com/conan/foobar/conan'])
        func(*args, **kwargs)
    return wrapper


class BintrayUpdaterEnvironmentTest(ConanClientTestCase):
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
        tools.save('conanfile.py', content=self.conanfile_base)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("pre_upload_recipe(): ERROR: Could not update Bintray info: username not found", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_unset_bintray_password(self):
        with tools.environment_append({"BINTRAY_USERNAME": "foobar"}):
            tools.save('conanfile.py', content=self.conanfile_base)
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("pre_upload_recipe(): ERROR: Could not update Bintray info: password not found", output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)


class BintrayUpdaterTest(ConanClientTestCase):
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

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_valid_upload(self):
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn("pre_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc issue_tracker_url labels licenses vcs_url website_url.", output)
        self.assertIn("pre_upload_recipe(): Bintray package information has been updated with success.", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_bad_oss_licenses(self):
        responses.add(responses.GET, "https://api.bintray.com/licenses/oss_licenses", status=500, json={"message": "You have reached a dark spot"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn('pre_upload_recipe(): ERROR: Could not request OSS licenses (500): {"message": "You have reached a dark spot"}', output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake'", output)

    @responses.activate
    @accept_conan_upload
    def test_bad_remote_address(self):
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
        self.assertNotIn("pre_upload_recipe(): Reading package info from Bintray.", output)
        self.assertNotIn("pre_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn('pre_upload_recipe(): ERROR: Could not extract subject and repo from https://api.fake.io: Invalid pattern', output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'badremote'", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_bad_package_info_request(self):
        responses.replace(responses.GET, 'https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', status=500, json={"message": "You have reached a dark spot"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn('ERROR: Could not request package info (500): {"message": "You have reached a dark spot"}', output)
        self.assertNotIn("pre_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_bad_patch_package_info(self):
        responses.replace(responses.PATCH, "https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar", status=500, json={"message": "You have reached a dark spot"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
        self.assertIn("pre_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc issue_tracker_url labels licenses vcs_url website_url.", output)
        self.assertIn('pre_upload_recipe(): ERROR: Could not patch package info: {"message": "You have reached a dark spot"}', output)
        self.assertNotIn("pre_upload_recipe(): Bintray package information has been updated with success.", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)


    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_stable_branch(self):
        with tools.environment_append({"TRAVIS": "TRUE", "TRAVIS_BRANCH": "release/0.1.0"}):
            tools.save('conanfile.py', content=self.conanfile_complete)
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
            self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
            self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
            self.assertIn("pre_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc issue_tracker_url labels licenses maturity vcs_url website_url.", output)
            self.assertIn("pre_upload_recipe(): Bintray package information has been updated with success.", output)
            self.assertNotIn('pre_upload_recipe(): ERROR', output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_stable_branch_pattern(self):
        with tools.environment_append({"TRAVIS": "TRUE", "TRAVIS_BRANCH": "tag/0.1.0", "CONAN_STABLE_BRANCH_PATTERN": "tag/*"}):
            tools.save('conanfile.py', content=self.conanfile_complete)
            self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
            output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
            self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
            self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
            self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
            self.assertIn("pre_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc issue_tracker_url labels licenses maturity vcs_url website_url.", output)
            self.assertIn("pre_upload_recipe(): Bintray package information has been updated with success.", output)
            self.assertNotIn('pre_upload_recipe(): ERROR', output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_unsafe_url(self):
        empty_package_response = {
            "desc":None,
            "labels":[],
            "licenses":[],
            "website_url":None,
            "issue_tracker_url":None,
            "vcs_url":None,
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
            self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
            self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
            self.assertIn("pre_upload_recipe(): Bintray is outdated. Updating Bintray package info: desc issue_tracker_url labels vcs_url website_url.", output)
            self.assertIn('pre_upload_recipe(): ERROR: Bad package URL: Only HTTPS is allowed, Bintray API uses Basic Auth', output)
            self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'unsafe': http://api.bintray.com/conan/foobar/conan", output)

    @responses.activate
    @accept_conan_upload
    @add_fake_remote
    def test_up_to_date_info(self):
        information = {
            "desc": "This a dummy library",
            "labels":["conan", "dummy", "qux", "baz"],
            "licenses":["MIT"],
            "website_url": "https://dummy.org",
            "issue_tracker_url":"https://github.com/foobar/community/issues",
            "vcs_url":"https://github.com/foobar/conan-dummy",
            "maturity":"Stable"
        }
        responses.replace(responses.GET, 'https://api.bintray.com/packages/foobar/conan/dummy%3Afoobar', json=information)
        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn("Uploading dummy/0.1.0@foobar/stable to remote 'fake'", output)
        self.assertIn("pre_upload_recipe(): Reading package info from Bintray.", output)
        self.assertIn("pre_upload_recipe(): Inspecting recipe info.", output)
        self.assertNotIn("pre_upload_recipe(): Bintray is outdated.", output)
        self.assertIn("pre_upload_recipe(): Bintray package info is up-to-date.", output)
        self.assertNotIn("pre_upload_recipe(): Bintray package information has been updated with success.", output)
        self.assertIn("Uploaded conan recipe 'dummy/0.1.0@foobar/stable' to 'fake': https://bintray.com/foobar/conan", output)
